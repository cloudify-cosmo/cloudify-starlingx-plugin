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

from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx

from .utils import (
    get_system,
    create_deployment,
    update_runtime_properties,
    get_controller_node_instance)


@workflow
def discover_subclouds(node_instance_id=None, node_id=None, ctx=None, **_):
    """ Discover subclouds of starlingx controllers.
    We either use a hint for a single controller or discover subclouds for
    all nodes in the deployment.  We get the controller objects, then we search
    those for subclouds related to that controller. We update the controller
    node instance runtime properties with a dict of related subclouds info.

    :param node_instance_id: The node instance ID to discover on.
    :param node_id: A node ID hint.
    :param ctx: Cloudify workflo context
    :param _: Additional kwargs, which we ignore.
    :return: None
    """

    # Todo: Check and see what needs to be done for rediscover.
    ctx = ctx or wtx
    controller_node_instance = get_controller_node_instance(
        node_instance_id, node_id, ctx=ctx)
    system = get_system(
        ctx.get_node(controller_node_instance.node_id))
    if not system.subcloud_resources:
        ctx.logger.error(
            'System {s} has no subclouds.'.format(s=system.resource_id))
    else:
        ctx.logger.info(
            'System {s} has subclouds. Storing...'.format(
                s=system.resource_id))
        update_runtime_properties(
            instance=controller_node_instance,
            resources=system.subcloud_resources,
            prop_name='subclouds')


@workflow
def deploy_subcloud(inputs, blueprint_id, deployment_id=None, ctx=None):
    ctx = ctx or wtx
    ctx.logger.info(
        'Creating deployment {dep} with blueprint {blu} '
        'with these inputs: {inp}'.format(
            dep=deployment_id, blu=blueprint_id, inp=inputs))
    create_deployment(inputs=inputs,
                      blueprint_id=blueprint_id,
                      deployment_id=deployment_id)


@workflow
def discover_and_deploy(node_id=None,
                        node_instance_id=None,
                        deployment_id=None,
                        blueprint_id=None,
                        ctx=None,
                        **_):

    # Todo: Make this idempotent
    # I.e. First, we do not discover the same cloud twice.
    # I.e. Second, we do not deploy the same cloud twice.
    # I.e. Check and see if discovered subclouds still exist.
    ctx = ctx or wtx
    discover_subclouds(node_instance_id=node_instance_id,
                       node_id=node_id,
                       ctx=ctx)
    controller_node_instance = get_controller_node_instance(
        node_instance_id, node_id, ctx=ctx)

    subclouds = controller_node_instance.runtime_properties.get(
        'subclouds', {})

    for subcloud in subclouds.values():
        subcloud_name = subcloud.get('name')
        deployment_id = deployment_id or subcloud_name
        # How do we get the system object for the subcloud?
        # system = get_system(ctx.get_node(subcloud_name))
        inputs = {
            'system_uuid': 'null',
            'system_name': subcloud_name,
            'distributed_cloud_role': 'subcloud',
            'system_type': 'null',
            'system_mode': 'null'
        }
        deploy_subcloud(
            blueprint_id=blueprint_id,
            deployment_id=deployment_id,
            inputs=inputs,
            ctx=ctx)
