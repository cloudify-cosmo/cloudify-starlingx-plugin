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

from copy import deepcopy

from cloudify.workflows import ctx as wtx
from cloudify.manager import get_rest_client
from cloudify.exceptions import NonRecoverableError


def with_rest_client(func):
    """
    :param class_decl: This is a class for the starlingx resource need to be
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
                node_instances.append(node_instance)
    return node_instances


@with_rest_client
def update_runtime_properties(rest_client,
                              instance,
                              resources,
                              prop_name):
    """

    :param rest_client: The rest client.
    :param instance: The node instance to update.
    :param resources: A list of resources to pull.
    :param prop_name: The property on the instance to update.
    :return:
    """

    prop_name = prop_name or 'subcloud'

    for resource in resources:
        props = deepcopy(instance.runtime_properties)
        prop = props.get(prop_name, {})
        if resource.resource_id not in prop:
            prop.update({resource.resource_id: resource.to_dict()})
        props[prop_name] = prop
        rest_client.nodeinstances.update(instance.id,
                                         instance.state,
                                         props,
                                         instance.state + 1)


def desecretize_client_config(config):
    for key, value in config.items():
        config[key] = check_for_secret_value(value)
    return config


def check_for_secret_value(prop):
    if isinstance(prop, dict):
        if 'get_secret' in prop:
            return get_secret(secret_name=prop.get('get_secret'))
    return prop


@with_rest_client
def get_secret(rest_client, secret_name):
    secret = rest_client.secrets.get(secret_name)
    return secret.value


@with_rest_client
def create_deployment(rest_client, inputs, blueprint_id, deployment_id=None):
    rest_client.deployments.create(
        blueprint_id, deployment_id or blueprint_id, inputs)
