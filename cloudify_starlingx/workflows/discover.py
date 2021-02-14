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

from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx
from cloudify.utils import exception_to_error_cause
from cloudify.exceptions import NonRecoverableError

from dcmanagerclient.exceptions import APIException
from cloudify_starlingx_sdk.resources.configuration import SystemResource

from .utils import (
    create_deployment,
    get_instances_of_nodes,
    update_runtime_properties,
    desecretize_client_config)

CONTROLLER_TYPE = 'cloudify.nodes.starlingx.SystemController'


@workflow
def discover_subclouds(node_id=None, ctx=None, **_):
    """ Discover subclouds of starlingx controllers.
    We either use a hint for a single controller or discover subclouds for
    all nodes in the deployment.  We get the controller objects, then we search
    those for subclouds related to that controller. We update the controller
    node instance runtime properties with a dict of related subclouds info.

    :param node_id: A node ID hint.
    :param ctx: Cloudify workflo context
    :param _: Additional kwargs, which we ignore.
    :return: None
    """

    ctx = ctx or wtx
    if node_id:
        controller_node = ctx.get_node(node_id)
        controller_node_instances = controller_node.instances
    else:
        controller_node_instances = get_instances_of_nodes(
            node_type=CONTROLLER_TYPE, deployment_id=ctx.deployment.id)

    for controller_node_instance in controller_node_instances:
        # For each node perform discover subcloud process
        subclouds = discover_subcloud(controller_node_instance)
        update_runtime_properties(
            controller_node_instance, subclouds, 'subcloud')


def discover_subcloud(controller_node):
    """ For a provided cloudify node object of controller type, we scan for
    related subclouds.

    :param controller_node: Cloudify node rest API object.
    :return list: subclouds
    """
    node = wtx.get_node(node_id=controller_node.node_id)
    client_config = desecretize_client_config(
            node.properties.get('client_config', {}))
    try:
        return SystemResource(
            client_config=client_config,
            resource_config=node.properties.get('resource_config'),
            logger=wtx.logger
        ).subcloud_resources
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
                ': {0}'.format(message))
        else:
            wtx.logger.error('No subclouds identified. {0}'.format(message))
        return []


@workflow
def deploy_subcloud(inputs, blueprint_id, deployment_id=None, ctx=None):
    ctx = ctx or wtx
    ctx.logger.info(
        'Creating Deployment {_did} from blueprint {_bid}.'.format(
            _bid=blueprint_id, _did=deployment_id or blueprint_id))
    create_deployment(inputs, blueprint_id, deployment_id)


@workflow
def discover_and_deploy(node_id=None, ctx=None):
    ctx = ctx or wtx
    discover_subclouds(node_id, ctx)
    