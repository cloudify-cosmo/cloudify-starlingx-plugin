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

import os
from urllib.parse import urlparse, urlunparse

from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx
from cloudify.exceptions import NonRecoverableError

from ..constants import LABELS
from ..utils import (
    get_system,
    get_deployment,
    is_ipv4_address,
    create_deployment,
    install_deployment,
    create_deployments,
    install_deployments,
    update_runtime_properties,
    get_controller_node_instance,
    get_parent_deployment_capabilities)


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
    if not controller_node_instance:
        ctx.logger.error('No system controller nodes were identified.')
        return False
    cafile, cafilename, system = get_system(
        ctx.get_node(controller_node_instance.node_id))
    if not system.subcloud_resources:
        ctx.logger.error(
            'System {s} has no subclouds.'.format(s=system.resource_id))
    else:
        update_runtime_properties(
            instance=controller_node_instance,
            resources=system.subcloud_resources,
            prop_name='subclouds')
    if cafile and cafilename:
        os.close(cafile)
        os.remove(cafilename)
    return True


@workflow
def deploy_subcloud(inputs,
                    labels,
                    blueprint_id,
                    deployment_id=None,
                    ctx=None):

    ctx = ctx or wtx
    ctx.logger.info(
        'Creating deployment {dep} with blueprint {blu} '
        'with these inputs: {inp}'.format(
            dep=deployment_id, blu=blueprint_id, inp=inputs))
    create_deployment(inputs=inputs,
                      labels=labels,
                      blueprint_id=blueprint_id,
                      deployment_id=deployment_id)
    ctx.logger.info('Installing deployment {dep}.'.format(dep=deployment_id))
    install_deployment(deployment_id)


@workflow
def deploy_subclouds(group_id,
                     blueprint_id,
                     deployment_ids,
                     inputs,
                     labels,
                     ctx=None):

    ctx = ctx or wtx
    ctx.logger.info(
        'Creating deployments {dep} with blueprint {blu} '
        'with these inputs: {inp} and labels {lab}'.format(
            dep=deployment_ids, blu=blueprint_id, inp=inputs, lab=labels))
    create_deployments(group_id, blueprint_id, deployment_ids, inputs, labels)
    install_deployments(group_id)


@workflow
def discover_and_deploy(node_id=None,
                        node_instance_id=None,
                        deployment_id=None,
                        blueprint_id=None,
                        ctx=None,
                        **_):

    def generate_deployment_id(subclouds_name):
        return '{sub}_{cid}'.format(
            sub=subclouds_name,
            cid=ctx.deployment.id
        )

    ctx = ctx or wtx
    blueprint_id = blueprint_id or ctx.blueprint.id
    discovered_subclouds = discover_subclouds(
        node_instance_id=node_instance_id,
        node_id=node_id,
        ctx=ctx)

    if not discovered_subclouds:
        return

    controller_node_instance = get_controller_node_instance(
        node_instance_id, node_id, ctx=ctx)

    parent_deployment_capabilities = get_parent_deployment_capabilities(
        deployment=get_deployment(ctx.deployment.id))
    auth_url = parent_deployment_capabilities.get('wrcp-ip', '')
    user_secret = parent_deployment_capabilities.get('wrcp-user-secret', '')
    password_secret = parent_deployment_capabilities.get(
        'wrcp-password-secret', '')
    cacert_secret = parent_deployment_capabilities.get(
        'wrcp-cacert-secret',
        '')
    wrcp_insecure = parent_deployment_capabilities.get(
        'wrcp-insecure',
        '')
    scheme, _, __, ___, ____, _____ = urlparse(auth_url)

    props = controller_node_instance.runtime_properties
    subclouds = props.get('subclouds', {})

    if deployment_id and len(subclouds) > 1:
        raise NonRecoverableError(
            'A deployment ID {dep} was provided, '
            'but more than one subcloud must be deployed. '
            'Either leave deployment ID blank, '
            'or ensure only one subcloud will be provided.'.format(
                dep=deployment_id))

    deployment_ids_list = []
    inputs_list = []
    labels_list = []

    for _, subcloud in subclouds.items():

        subcloud_name = subcloud.get('name')

        _deployment_id = deployment_id or generate_deployment_id(subcloud_name)

        if get_deployment(_deployment_id):
            ctx.logger.info(
                'A deployment for subcloud {sub} {dep} already exists.'.format(
                    sub=subcloud_name, dep=_deployment_id))
            continue

        # How do we get the system object for the subcloud?
        ip = subcloud.get('oam_floating_ip')
        if is_ipv4_address(ip):
            new_netloc = '{ip}:5000'.format(ip=ip)
        else:
            new_netloc = '[{ip}]:5000'.format(ip=ip)

        inputs = {
            'auth_url': urlunparse((scheme, new_netloc, '/v3', '', '', '')),
            'user_secret': user_secret,
            'password_secret': password_secret,
            'cacert_secret': cacert_secret,
            'insecure': wrcp_insecure,
            'region_name': subcloud_name
        }

        labels = [{'csys-env-type': LABELS['types']['subcloud']},
                  {'wrcp-group-id': str(subcloud.get('group_id'))},
                  {'csys-obj-parent': ctx.deployment.id}]
        deployment_ids_list.append(_deployment_id)
        inputs_list.append(inputs)
        labels_list.append(labels)

    deploy_subclouds(ctx.deployment.id,
                     blueprint_id,
                     deployment_ids_list,
                     inputs_list,
                     labels_list,
                     ctx)
