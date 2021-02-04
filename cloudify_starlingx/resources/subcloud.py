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

from ..decorators import with_starlingx_resource
from cloudify_starlingx_sdk.resources.distributed_cloud import SubcloudResource


def preconfigure(_, ctx):
    ctx.source.instance.runtime_properties['controller_region_name'] = \
        ctx.target.node.properties['client_config']['region_name']


@with_starlingx_resource(SubcloudResource)
def poststart(resource, ctx):
    resource.client_config['region_name'] = \
        ctx.instance.runtime_properties['controller_region_name']
    subcloud = resource.get()
    ctx.instance.runtime_properties['external_id'] = subcloud.resource_id
    ctx.instance.runtime_properties['name'] = subcloud.name
    ctx.instance.runtime_properties['location'] = subcloud.location
    ctx.instance.runtime_properties['description'] = subcloud.description
    ctx.instance.runtime_properties['group_id'] = \
        subcloud.group_id
    ctx.instance.runtime_properties['oam_floating_ip'] = \
        subcloud.oam_floating_ip
    ctx.instance.runtime_properties['management_state'] = \
        subcloud.management_state
