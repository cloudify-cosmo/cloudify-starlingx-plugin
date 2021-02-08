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

from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx

from cloudify_starlingx_sdk.resources.configuraton import ISystemResource
from cloudify_starlingx_sdk.resources.distributed_cloud import SubcloudResource

from .utils import import get_instances_of_nodes, update_runtime_properties

CONTROLLER_TYPE = 'cloudify.nodes.starlingx.Controller'


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
    controller_node_instances = get_instances_of_nodes(
        node_id, CONTROLLER_TYPE)

    for controller_node_instance in controller_node_instances:
        # For each node perform discover subcloud process
        subclouds = discover_subcloud(controller_node_instance)
        update_runtime_properties(controller_node_instance, subclouds)


def discover_subcloud(controller_node):
    """ For a provided cloudify node object of controller type, we scan for
    related subclouds.

    :param controller_node: Cloudify node rest API object.
    :return list: subclouds
    """

    controller = ISystemResource(
        client_config=controller_node.properties.get('client_config'),
        resource_config=controller_node.properties.get('resource_config'),
        logger=wtx.logger
    )
    subcloud = SubcloudResource(
        client_config=controller_node.properties.get('client_config'),
        logger=wtx.logger
    )
    subcloud.client_config['region_name'] = controller.region_name
    return subcloud.list()
