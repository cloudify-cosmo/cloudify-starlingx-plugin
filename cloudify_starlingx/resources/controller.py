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

from cloudify.exceptions import NonRecoverableError

from ..decorators import with_starlingx_resource
from ..utils import update_prop_resource, update_prop_resources
from cloudify_starlingx_sdk.resources.configuration import SystemResource


@with_starlingx_resource(SystemResource)
def poststart(resource, ctx):
    """ Read a system resource and store its properties in the node instance
    runtime properties.

    :param resource: A system resource.
    :param ctx: The Cloudify context.
    :return:
    """

    # Collect basic info: distributed_cloud_role, uuid, name, system mode/type
    update_prop_resource(ctx.instance, resource)
    update_prop_resources(ctx.instance, resource.host_resources, 'hosts')
    # If subcloud, collect oam_floating_ip, management_state, etc.
    if resource.is_subcloud:
        update_prop_resource(
            ctx.instance, resource.subcloud_resource, 'subcloud')
    # If controller, gather subclouds info.
    elif resource.is_system_controller:
        update_prop_resources(
            ctx.instance, resource.subcloud_resources, 'subclouds')
    # The only other option is a standalone system. If that's not the case,
    # we should fail, because it's not a supported scenario.
    elif not resource.is_standalone_system:
        raise NonRecoverableError(
            'Unsupported system type: '
            'the system is neither a standalone system, system controller, '
            'nor a subcloud.')
