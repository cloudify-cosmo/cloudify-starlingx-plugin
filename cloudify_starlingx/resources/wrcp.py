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

from cloudify.exceptions import NonRecoverableError

from ..constants import LABELS, DEFAULT_REGION
from ..decorators import with_starlingx_resource
from ..utils import (
    assign_site,
    add_new_label,
    get_parent_wrcp_ip,
    update_prop_resource,
    update_prop_resources,
    assign_required_labels,
    update_openstack_props,
    update_kubernetes_props)
from cloudify_starlingx_sdk.resources.configuration import SystemResource
from cloudify_starlingx_sdk.resources.distributed_cloud import SubcloudResource


@with_starlingx_resource(SystemResource)
def poststart(resource, ctx):
    """ Read a system resource and store its properties in the node instance
    runtime properties.

    :param resource: A system resource.
    :param ctx: The Cloudify context.
    :return:
    """

    if resource.is_subcloud:
        update_subcloud_resource(resource,
                                 ctx.instance,
                                 ctx.deployment.id)
        add_new_label('csys-env-type',
                      LABELS['types']['subcloud'],
                      ctx.deployment.id)
    elif resource.is_system_controller:
        if 'subcloud_names' not in ctx.instance.runtime_properties:
            ctx.instance.runtime_properties['subcloud_names'] = []
        for subcloud_name in resource.subcloud_resource_names:
            ctx.instance.runtime_properties['subcloud_names'].append(
                subcloud_name)
        # update_prop_resources(
        #     ctx.instance, resource.subcloud_resources, 'subclouds')
        add_new_label('csys-env-type',
                      LABELS['types']['systemcontroller'],
                      ctx.deployment.id)
    elif not resource.is_standalone_system:
        raise NonRecoverableError(
            'Unsupported system type: '
            'the system is neither a standalone system, system controller, '
            'nor a subcloud.')
    else:
        add_new_label('csys-env-type',
                      LABELS['types']['default'],
                      ctx.deployment.id)

    update_prop_resource(ctx.instance, resource)
    update_prop_resources(ctx.instance, resource.host_resources, 'hosts')
    update_prop_resources(
        ctx.instance, resource.kube_cluster_resources, 'kube_clusters')
    update_kubernetes_props(ctx.instance, resource.kube_cluster_resources)
    update_openstack_props(ctx.instance,
                           resource.openstack_cluster_resource,
                           resource.client_config)
    assign_required_labels(ctx.instance, ctx.deployment.id)
    assign_site(ctx.instance, ctx.deployment.id, resource.location)


@with_starlingx_resource(SystemResource)
def start(resource, ctx):
    """
    It lists all available patches.
    """
    resource.patches_list()


def get_subcloud_resource(resource, deployment_id):
    parent_ip = get_parent_wrcp_ip(deployment_id)
    if parent_ip:
        client_config = deepcopy(resource.client_config)
        subcloud_id = client_config.get(
            'region_name', client_config.get('os_region_name'))
        if 'os_auth_url' in client_config:
            del client_config['os_auth_url']
        if 'os_region_name' in client_config:
            del client_config['os_region_name']
        client_config['auth_url'] = parent_ip
        client_config['region_name'] = DEFAULT_REGION
        subcloud_resource = SubcloudResource(
            client_config=client_config,
            resource_config={'subcloud_id': subcloud_id},
            logger=resource.logger)
        return subcloud_resource
    resource.logger.error(
        'Parent IP was not provided and is required to set '
        'oam_floating_ip and other subcloud values.')


def update_subcloud_resource(resource, ctx_instance, deployment_id):
    subcloud_resource = get_subcloud_resource(resource, deployment_id)
    if subcloud_resource:
        ctx_instance.runtime_properties['oam_floating_ip'] = \
            subcloud_resource.oam_floating_ip
        update_prop_resource(
            ctx_instance, subcloud_resource, 'subcloud')


