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


import sys
from time import sleep
from copy import deepcopy

from cloudify.workflows import ctx as wtx
from cloudify.manager import get_rest_client
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause
from dcmanagerclient.exceptions import APIException
from cloudify_rest_client.exceptions import (
    CloudifyClientError,
    DeploymentEnvironmentCreationPendingError)

from cloudify_starlingx_sdk.resources.configuration import SystemResource

CONTROLLER_TYPE = 'cloudify.nodes.starlingx.System'


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
def get_node_instances_by_type(node_type, deployment_id, rest_client):
    """Filter node instances by type.

    :param rest_client: The rest client.
    :param node_type: the node type that we wish to filter.
    :param deployment_id: The deployment ID.
    :return list: a list of node instances.
    """
    node_instances = []
    for node in rest_client.nodes.list(deployment_id=deployment_id):
        if node_type in node.type_hierarchy:
            for node_instance in rest_client.node_instances.list(
                    node_id=node.id):
                if node_instance.state != 'started':
                    continue
                node_instances.append(node_instance)
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

    for resource in resources:
        props = deepcopy(instance.runtime_properties)
        prop = props.get(prop_name, {})
        if resource.resource_id not in prop:
            prop.update(**resource.to_dict())
        props[prop_name] = prop
        rest_client.node_instances.update(instance.id,
                                          instance.state,
                                          props,
                                          int(instance.version) + 1)


def desecretize_client_config(config):
    for key, value in config.items():
        config[key] = resolve_intrinsic_functions(value)
    return config


def resolve_intrinsic_functions(prop):
    if isinstance(prop, dict):
        if 'get_secret' in prop:
            prop = prop.get('get_secret')
            if isinstance(prop, dict):
                prop = resolve_intrinsic_functions(prop)
            return get_secret(prop)
        if 'get_input' in prop:
            prop = prop.get('get_input')
            if isinstance(prop, dict):
                prop = resolve_intrinsic_functions(prop)
            return get_input(prop)
    return prop


@with_rest_client
def get_secret(secret_name, rest_client):
    secret = rest_client.secrets.get(secret_name)
    return secret.value


@with_rest_client
def create_deployment(inputs, blueprint_id, deployment_id, rest_client):
    rest_client.deployments.create(
        blueprint_id, deployment_id or blueprint_id, inputs)


@with_rest_client
def install_deployment(deployment_id, rest_client):
    attempts = 0
    while True:
        try:
            rest_client.executions.start(deployment_id, 'install')
        except DeploymentEnvironmentCreationPendingError:
            attempts += 1
            sleep(5)
            pass
        else:
            break


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
        raise NonRecoverableError(
            'Expected only one node SystemController node instance. '
            'Exactly {ll} were found: [{nn}]. '
            'Provide the ID of a specific SystemController node instance '
            'using the node_instance_id parameter.'.format(
                ll=len(controllers),
                nn=controllers))

    return controllers[0]


def get_system(controller_node):
    """ Get a system object by cloudify node.

    :param controller_node: Cloudify node rest API object.
    :return list: subclouds
    """
    client_config = desecretize_client_config(
        controller_node.properties.get('client_config', {}))
    try:
        return SystemResource(
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
        return
