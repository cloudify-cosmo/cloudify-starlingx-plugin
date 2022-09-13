# #######
# Copyright (c) 2021 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import sys
import time
import base64
import asyncio
from time import sleep
from copy import deepcopy
from tempfile import mkstemp
from urllib.parse import urlparse
from ipaddress import ip_address, IPv4Address

from cloudify import ctx
from cloudify.workflows import ctx as wtx
from cloudify.manager import get_rest_client
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause
from dcmanagerclient.exceptions import APIException
from cloudify_rest_client.exceptions import (
    CloudifyClientError,
    DeploymentEnvironmentCreationPendingError,
    DeploymentEnvironmentCreationInProgressError)
from cloudify.constants import NODE_INSTANCE, RELATIONSHIP_INSTANCE

from cloudify_starlingx_sdk.common import StarlingXException
from cloudify_starlingx_sdk.resources.configuration import SystemResource

CONTROLLER_TYPE = 'cloudify.nodes.starlingx.WRCP'


def background(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop(
            ).run_in_executor(None, f, *args, **kwargs)
    return wrapped


def resolve_node_ctx_from_relationship(_ctx):
    """
    This method is to decide where to get node from relationship context
    since this is not exposed correctly from cloudify
    :param _ctx: current cloudify context object
    :return: RelationshipSubjectContext instance
    """
    # Get the node_id for the current node in order to decide if that node
    # is source | target
    node_id = _ctx._context.get('node_id')

    source_node_id = _ctx.source._context.get('node_id')
    target_node_id = _ctx.target._context.get('node_id')

    if node_id == source_node_id:
        return _ctx.source
    elif node_id == target_node_id:
        return _ctx.target
    else:
        raise NonRecoverableError(
            'Unable to decide if current node is source or target')


def resolve_ctx(_ctx):
    """
    This method is to lookup right context instance which could be one of
    the following:
     1- Context for source relationship instance
     2- Context for target relationship instance
     3- Context for current node
    :param _ctx: current cloudify context object
    :return: This could be RelationshipSubjectContext or CloudifyContext
    instance
    """
    if _ctx.type == RELATIONSHIP_INSTANCE:
        return resolve_node_ctx_from_relationship(_ctx)
    if _ctx.type != NODE_INSTANCE:
        _ctx.logger.warn(
            'CloudifyContext is neither {0} nor {1} type. '
            'Falling back to {0}. This indicates a problem.'.format(
                NODE_INSTANCE, RELATIONSHIP_INSTANCE))
    return _ctx


def update_prop_resource(ctx_instance, resource, config_key=None):
    config_key = config_key or 'resource_config'
    resource_config = ctx_instance.runtime_properties.get(config_key, {})
    resource_config.update(resource.to_dict())
    ctx_instance.runtime_properties[config_key] = resource_config
    ctx_instance.update()


def update_prop_resources(ctx_instance, resources, config_key=None):
    for resource in resources:
        update_prop_resource(ctx_instance, resource, config_key)


def update_kubernetes_props(ctx_instance, resources):
    if resources:
        cluster = resources[0]
        ctx_instance.runtime_properties['k8s_cluster_name'] = \
            cluster.resource.cluster_name
        ctx_instance.runtime_properties['k8s_admin_user'] = \
            cluster.resource.admin_user
        ctx_instance.runtime_properties['k8s_ip'] = \
            cluster.resource.cluster_api_endpoint
        if cluster.resource.admin_token:
            ctx_instance.runtime_properties['k8s_service_account_token'] = \
                base64.b64decode(cluster.resource.admin_token).decode('utf-8')
        else:
            ctx_instance.runtime_properties['k8s_service_account_token'] = \
                ''
        ctx_instance.runtime_properties['k8s_cacert'] = \
            cluster.resource.cluster_ca_cert
        ctx_instance.runtime_properties['k8s_admin_client_cert'] = \
            cluster.resource.admin_client_cert
        ctx_instance.runtime_properties['k8s_admin_client_key'] = \
            cluster.resource.admin_client_key


def update_openstack_props(ctx_instance, resources, client_config):
    if resources:
        cluster = resources[0]
        ctx_instance.runtime_properties['openstack_ip'] = \
            cluster.resource.value
        ctx_instance.runtime_properties['openstack_key'] = \
            client_config.get('api_key',
                              client_config.get('password',
                                                client_config.get(
                                                    'os_password')))


def assign_site(ctx_instance, deployment_id, location):
    config = ctx_instance.runtime_properties.get('resource_config', {})
    location_name = format_location_name(config.get('location', ''))
    ctx.logger.debug('Location name {0} location {1}'.format(
        location_name, location))
    x, y = location.split(',')
    if not isinstance(x, float) and isinstance(y, float):
        ctx.logger.error('Invalid location data provided. Not creating site.')
        return
    if 'none' in location.lower():
        ctx.logger.error('Invalid location data provided. Not creating site.')
        return
    site = get_site(location_name)
    if not site:
        create_site(location_name, location)
    elif not site.get('location'):
        update_site(location_name, location)
    update_deployment_site(deployment_id, location_name)


def format_location_name(location_name):
    return re.sub('\\-+', '-', re.sub('[^0-9a-zA-Z]', '-', str(location_name)))


def get_subcloud_group_id_and_name(ctx_instance):
    # There is really only one subcloud here,
    # but it's nested in a dict with one item.
    # I prefer to do it this way instead of trying KeyError. Just looks better
    # IMO.
    subclouds = ctx_instance.runtime_properties.get('subcloud')
    if subclouds:
        for subcloud in subclouds.values():
            return subcloud.get('group_id', 'null'),\
                   subcloud.get('group_name', 'null')
    return ('null', 'null')


def assign_required_labels(ctx_instance, deployment_id):

    labels = get_deployment_labels(deployment_id)
    config = ctx_instance.runtime_properties.get('resource_config', {})
    group_id, group_name = get_subcloud_group_id_and_name(ctx.instance)

    services = []
    if ctx_instance.runtime_properties.get('k8s_ip'):
        services.append('kubernetes')
    if ctx_instance.runtime_properties.get('openstack_ip'):
        services.append('openstack')
    services = tuple(services)

    labels['csys-location-name'] = str(config.get('location'))
    labels['csys-location-lat'] = str(config.get('latitude'))
    labels['csys-location-long'] = str(config.get('longitude'))
    if group_id != 'null':
        labels['wrcp-group-id'] = str(group_id)
    if group_name != 'null':
        labels['wrcp-group-name'] = group_name
    if services:
        labels['csys-wrcp-services'] = services
    ctx.logger.info(labels)
    update_deployment_labels(deployment_id, labels)


def get_parent_wrcp_ip(deployment_id=None, deployment=None):
    deployment_capabilities = get_parent_deployment_capabilities(
        deployment_id, deployment)
    return deployment_capabilities.get('wrcp-ip', '')


def get_parent_deployment_capabilities(deployment_id=None, deployment=None):
    caps = {}
    if deployment_id and not deployment:
        deployment = get_parent_deployment(deployment_id)
    if deployment:
        for key, cap in deployment.capabilities.items():
            caps[key] = resolve_intrinsic_functions(
                cap['value'], deployment_id)
    return caps


def with_rest_client(func):
    """
    :param func: This is a class for the starlingx resource need to be
    invoked
    :return: a wrapper object encapsulating the invoked function
    """

    def wrapper_inner(*args, **kwargs):
        kwargs['rest_client'] = get_rest_client()
        return func(*args, **kwargs)
    return wrapper_inner


def get_instances_of_nodes(node_id=None, node_type=None, deployment_id=None):
    """ Get instances of nodes either by node ID or node type.

    :param node_id: The node ID to filter.
    :param node_type: The node type to filter.
    :param deployment_id: The ID of a deployment node.
    :return list: A list of node instances.
    """
    if node_id:
        controller_node = wtx.get_node(node_id)
        return controller_node.instances
    elif node_type:
        return get_node_instances_by_type(
            node_type=node_type, deployment_id=deployment_id)
    else:
        raise NonRecoverableError('No node_id and no node_type provided.')


@with_rest_client
def get_site(site_name, rest_client):
    try:
        return rest_client.sites.get(site_name)
    except CloudifyClientError:
        return


@with_rest_client
def create_site(site_name, location, rest_client):
    return rest_client.sites.create(site_name, location)


@with_rest_client
def update_site(site_name, location, rest_client):
    return rest_client.sites.update(site_name, location)


@with_rest_client
def update_deployment_site(deployment_id, site_name, rest_client):
    deployment = get_deployment(deployment_id)
    if deployment.site_name == site_name:
        return deployment
    elif deployment.site_name:
        return rest_client.deployments.set_site(
            deployment_id, detach_site=True)
    return rest_client.deployments.set_site(
        deployment_id, site_name)


@with_rest_client
def get_controller_node(deployment_id, rest_client=None):
    """Get nodes by node type. There should be one.

    :param node_type:
    :param deployment_id:
    :param rest_client:
    :return:
    """
    nodes = []
    for node in rest_client.nodes.list(deployment_id=deployment_id,
                                       _includes=['properties']):
        if CONTROLLER_TYPE in node.type_hierarchy:
            nodes.append(node)
    if nodes:
        return nodes[0]
    raise NonRecoverableError(
        'No nodes of type {t} were found.'.format(t=CONTROLLER_TYPE))


@with_rest_client
def get_node_instances_by_type(node_type, deployment_id, rest_client):
    """Filter node instances by type.

    :param rest_client: The rest client.
    :param node_type: the node type that we wish to filter.
    :param deployment_id: The deployment ID.
    :return list: a list of node instances.
    """
    node_instances = []
    for ni in rest_client.node_instances.list(deployment_id=deployment_id,
                                              state='started',
                                              _includes=['id',
                                                         'state',
                                                         'version',
                                                         'runtime_properties',
                                                         'node_id']):
        node = rest_client.nodes.get(
            node_id=ni.node_id, deployment_id=deployment_id)
        if node_type in node.type_hierarchy:
            node_instances.append(ni)
    return node_instances


@with_rest_client
def update_runtime_properties(instance,
                              resources,
                              prop_name,
                              rest_client):
    """

    :param instance: The node instance to update.
    :param resources: A list of resources to pull.
    :param prop_name: The property on the instance to update.
    :param rest_client: The rest client.
    :return:
    """

    props = deepcopy(instance.runtime_properties)
    prop = props.get(prop_name, {})
    for resource in resources:
        if resource.resource_id not in prop:
            try:
                prop.update(**resource.to_dict())
            except (APIException, StarlingXException):
                try:
                    ctx.logger.error(
                        'Failed to get details of subcloud {}.'.format(
                            resource.resource_id))
                    raise
                except Exception:
                    wtx.logger.error(
                        'Skipping discovery of subcloud {}.'.format(
                            resource.resource_id))
                    continue
    props[prop_name] = prop
    instance_version = int(instance.version)
    rest_client.node_instances.update(node_instance_id=instance.id,
                                      state=instance.state,
                                      runtime_properties=props,
                                      version=instance_version)


def desecretize_client_config(config):
    for key, value in config.items():
        config[key] = resolve_intrinsic_functions(value)
    return config


def resolve_intrinsic_functions(prop, dep_id=None):
    if isinstance(prop, dict):
        if 'get_secret' in prop:
            prop = prop.get('get_secret')
            if isinstance(prop, dict):
                prop = resolve_intrinsic_functions(prop, dep_id)
            return get_secret(prop)
        if 'get_input' in prop:
            prop = prop.get('get_input')
            if isinstance(prop, dict):
                prop = resolve_intrinsic_functions(prop, dep_id)
            return get_input(prop)
        if 'get_attribute' in prop:
            prop = prop.get('get_attribute')
            if isinstance(prop, dict):
                prop = resolve_intrinsic_functions(prop, dep_id)
            node_id = prop[0]
            runtime_property = prop[1]
            return get_attribute(node_id, runtime_property, dep_id)
    return prop


@with_rest_client
def get_secret(secret_name, rest_client):
    secret = rest_client.secrets.get(secret_name)
    return secret.value


def add_new_label(key, value, deployment_id):
    labels = get_deployment_labels(deployment_id)
    labels[key] = value
    update_deployment_labels(deployment_id, labels)


def convert_list_to_dict(labels):
    labels = deepcopy(labels)
    target_dict = {}
    for label in labels:
        target_dict[label['key']] = label['value']
    return target_dict


def convert_dict_to_list(labels):
    labels = deepcopy(labels)
    target_list = []
    for key, value in labels.items():
        target_list.append({key: value})
    return target_list


def get_deployment_labels(deployment_id):
    deployment = get_deployment(deployment_id)
    return convert_list_to_dict(deepcopy(deployment.labels))


def get_deployment_label_by_name(label_name, deployment_id):
    labels = get_deployment_labels(deployment_id)
    return labels.get(label_name)


@with_rest_client
def get_parent_deployment(deployment_id, rest_client):
    deployment_id = get_deployment_label_by_name(
        'csys-obj-parent', deployment_id)
    if not deployment_id:
        ctx.logger.warn(
            'Unable to get parent deployment. '
            'No "csys-obj-parent" label set for deployment. '
            'Assuming manual subcloud enrollment. Set label manually.')
        return
    return rest_client.deployments.get(deployment_id)


@with_rest_client
def update_deployment_labels(deployment_id, labels, rest_client):
    labels = convert_dict_to_list(labels)
    ctx.logger.info(labels)
    rest_client.deployments.update_labels(
        deployment_id,
        labels=labels)


@with_rest_client
def create_deployments(group_id,
                       blueprint_id,
                       deployment_ids,
                       inputs,
                       labels,
                       rest_client):
    """Create a deployment group and create deployments in it.
    :param group_id:
    :param blueprint_id:
    :param deployment_ids:
    :param inputs:
    :param labels:
    :param rest_client:
    :return:
    """

    @background
    def create_deployment_background(blueprint_id, dep_id, inp, label):
        rest_client.deployments.create(
            blueprint_id,
            dep_id,
            inputs=inp,
            labels=label)
        c = 0
        while True:
            if get_deployment(dep_id):
                break
            time.sleep(2)
            c += 1
            if c >= 15:
                raise NonRecoverableError(
                    'Failed to create deployment {}'.format(dep_id))

    rest_client.deployment_groups.put(
        group_id=group_id,
        blueprint_id=blueprint_id)
    try:
        rest_client.deployment_groups.add_deployments(
            group_id,
            new_deployments=[
                {
                    'display_name': dep_id,
                    'inputs': inp,
                    'labels': label
                } for dep_id, inp, label in zip(
                    deployment_ids, inputs, labels)]
        )
    except TypeError:
        for dep_id, inp, label in zip(deployment_ids, inputs, labels):
            create_deployment_background(
                blueprint_id,
                dep_id,
                inputs=inp,
                labels=label)
        rest_client.deployment_groups.add_deployments(
            group_id,
            deployment_ids=deployment_ids)


@with_rest_client
def get_attribute(node_id, runtime_property, deployment_id, rest_client):
    for node_instance in rest_client.node_instances.list(node_id=node_id):
        if node_instance.deployment_id != deployment_id:
            continue
        return node_instance.runtime_properties.get(runtime_property)


@with_rest_client
def install_deployment(deployment_id, rest_client):
    attempts = 0
    while True:
        try:
            return rest_client.executions.start(deployment_id, 'install')
        except (DeploymentEnvironmentCreationPendingError,
                DeploymentEnvironmentCreationInProgressError) as e:
            attempts += 1
            if attempts > 15:
                raise NonRecoverableError(
                    'Maximum attempts waiting '
                    'for deployment {deployment_id}" {e}.'.format(
                        deployment_id=deployment_id, e=e))
            sleep(5)
            continue


@with_rest_client
def install_deployments(group_id, rest_client):
    attempts = 0
    while True:
        try:
            return rest_client.execution_groups.start(group_id, 'install')
        except (DeploymentEnvironmentCreationPendingError,
                DeploymentEnvironmentCreationInProgressError) as e:
            attempts += 1
            if attempts > 15:
                raise NonRecoverableError(
                    'Maximum attempts waiting '
                    'for deployment group {group}" {e}.'.format(
                        group=group_id, e=e))
            sleep(5)
            continue


@with_rest_client
def get_deployments_from_group(group, rest_client):
    attempts = 0
    while True:
        try:
            return rest_client.deployment_groups.get(group)
        except CloudifyClientError as e:
            attempts += 1
            if attempts > 15:
                raise NonRecoverableError(
                    'Maximum attempts waiting '
                    'for deployment group {group}" {e}.'.format(
                        group=group, e=e))
            sleep(5)
            continue


@with_rest_client
def create_deployment(inputs,
                      labels,
                      blueprint_id,
                      deployment_id,
                      rest_client):

    rest_client.deployments.create(
        blueprint_id, deployment_id, inputs, labels=labels)


@with_rest_client
def get_node_instance(node_instance_id, rest_client):
    return rest_client.node_instance.get(node_instance_id=node_instance_id)


@with_rest_client
def get_deployment(deployment_id, rest_client):
    try:
        return rest_client.deployments.get(deployment_id=deployment_id)
    except CloudifyClientError:
        return


@with_rest_client
def check_if_subcloud_discovered_and_deployed(display_name,
                                              parent_id,
                                              rest_client):
    """ See if a subcloud has already been discovered and deployed.
    This does provide idempotent behavior on manually registered subclouds.

    :param display_name:
    :param parent_id:
    :param rest_client:
    :return:
    """
    return {'display_name': display_name} in rest_client.deployments.list(
            _include=['display_name'],
            filter_rules=[
                {'type': 'label',
                 'operator': 'any_of',
                 'key': 'csys-obj-parent',
                 'values': [parent_id]
                 }
            ])


@with_rest_client
def get_input(input_name, rest_client):
    deployment = rest_client.deployments.get(wtx.deployment.id)
    return deployment.inputs.get(input_name)


def get_controller_node_instance(node_instance_id=None,
                                 node_id=None,
                                 ctx=None):

    """Get a node instance of a System Controller.

    :param node_instance_id:
    :param node_id:
    :param ctx:
    :return:
    """

    ctx = ctx or wtx
    if node_instance_id:
        node_instances = [get_node_instance(
            node_instance_id=node_instance_id)]
    elif node_id:
        controller_node = ctx.get_node(node_id)
        node_instances = controller_node.instances
    else:
        node_instances = get_instances_of_nodes(
            node_type=CONTROLLER_TYPE, deployment_id=ctx.deployment.id)

    controllers = []
    for node_instance in node_instances:
        resource_config = node_instance.runtime_properties.get(
            'resource_config', {})
        distributed_cloud_role = resource_config.get(
            'distributed_cloud_role', '')
        if not isinstance(distributed_cloud_role, str):
            distributed_cloud_role = str(distributed_cloud_role)
        if distributed_cloud_role == 'systemcontroller':
            controllers.append(node_instance)

    if len(controllers) != 1:
        ctx.logger.debug(
            'Expected only one node SystemController node instance. '
            'Exactly {ll} were found: [{nn}]. '
            'Provide the ID of a specific SystemController node instance '
            'using the node_instance_id parameter.'.format(
                ll=len(controllers),
                nn=controllers))
        return

    return controllers[0]


def handle_cert_in_config(client_config):
    """If https, we need a cert, and we need the file path. However,
    users pass this as a string. (No files from users thanks!)
    So, we need to get the cert, and write it as file.

    :param client_config:
    :return: (tuple):
      cacert: the ca material, for validating the auth URL.
      cafile: the file pointer, for closing the file later.
      cafilename: the path to make sure it gets deleted.
    """

    # Find out if we have http, so that we know to make sure that ca is not
    # sent.
    http = 'http://' in client_config['auth_url']
    # Set defaults so that we can send None values back using names.
    cacert = ''
    cafile = None
    cafilename = None
    insecure = client_config.pop('insecure', None)

    # We should never have these keys if http.
    if http:
        client_config.pop('cacert', None)
        client_config.pop('os_cacert', None)

    elif 'cacert' in client_config:
        cacert = client_config.get('cacert')
        cafile, cafilename = \
            cacert_as_file(cacert)
        client_config['cacert'] = cafilename
    elif 'os_cacert' in client_config:
        cacert = client_config.get('os_cacert')
        cafile, cafilename = \
            cacert_as_file(cacert)
        client_config['os_cacert'] = cafilename

    if not http and insecure and cacert:
        client_config['insecure'] = insecure

    return cacert, cafile, cafilename


def get_system(controller_node):
    """ Get a system object by cloudify node.

    :param controller_node: Cloudify node rest API object.
    :return list: subclouds
    """
    client_config = desecretize_client_config(
        controller_node.properties.get('client_config', {}))
    _, cafile, cafilename = handle_cert_in_config(client_config)
    try:
        return cafile, cafilename, SystemResource(
            client_config=client_config,
            resource_config=controller_node.properties.get('resource_config'),
            logger=wtx.logger
        )
    except APIException as errors:
        _, _, tb = sys.exc_info()
        if hasattr(errors, 'message'):
            message = errors.message
        else:
            message = ''
        message += str([exception_to_error_cause(errors, tb)])
        if 'Subcloud not found' not in message:
            raise NonRecoverableError(
                'Failure while trying to discover subclouds:'
                ' {0}'.format(message))


def cacert_as_file(cacert):
    if not isinstance(cacert, str):
        raise NonRecoverableError('The CA certificate must be as string.')
    new_file, filename = mkstemp()
    with open(filename, 'w') as outfile:
        outfile.write(cacert)
    return new_file, filename


def is_ipv4_address(ip):
    if type(ip_address(ip)) is IPv4Address:
        return True
    elif ip.startswith('[') or ip.endswith(']'):
        return True
    return False


def validate_auth_url(auth_url, ca=None, insecure=False):
    """ Give the user helpful error messages if we receive a combination
    that makes no sense.

    :param auth_url:
      A string in the form [protocol://] [IPv4 or IPv6 URL] [:PORT 5000] [/v3]
    :param ca: The string content of the ca.
    :param insecure: Whether the user intends to ignore SSL validation.
    :return:
    """
    scheme, netloc, endpoint, ___, ____, _____ = urlparse(auth_url)
    message = 'The provided auth_url {au} is' \
              ' invalid for the following reasons:\n'.format(au=auth_url)
    error = False
    if scheme not in ['https', 'http']:
        error = True
        message += ' - auth_url does not provide a protocol in ' \
                   '[http://, https://].\n'
    if ':5000' not in auth_url:
        error = True
        message += ' - auth_url does not provide a port in ' \
                   '[:5000].\n'
    if '/v3' not in auth_url:
        error = True
        message += ' - auth_url does not provide a path in ' \
                   '[v3].\n'
    if 'https://' in auth_url and not ca and insecure is False:
        error = True
        message += ' - insecure is False, CA is not provided, ' \
                   'but protocol is https.\n'
    if 'http://' in auth_url and insecure:
        error = True
        message += ' - the protocol is http, but insecure is True.\n'
    if 'http://' in auth_url and ca:
        error = True
        message += ' - the protocol is http, but a CA is provided.\n'

    if error:
        raise NonRecoverableError(message)
