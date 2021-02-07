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
from cloudify_starlingx_sdk.resources.configuration import ISystemResource


@with_starlingx_resource(ISystemResource)
def poststart(resource, ctx):
    isystem = resource.get()
    ctx.instance.runtime_properties['external_id'] = isystem.resource_id
    ctx.instance.runtime_properties['name'] = isystem.name
    ctx.instance.runtime_properties['location'] = isystem.location
    ctx.instance.runtime_properties['description'] = isystem.description
    ctx.instance.runtime_properties['system_type'] = isystem.system_type
    ctx.instance.runtime_properties['system_mode'] = isystem.system_mode
    ctx.instance.runtime_properties['region_name'] = isystem.region_name
    ctx.instance.runtime_properties['latitude'] = \
        getattr(isystem, 'latitude', None)
    ctx.instance.runtime_properties['longitude'] = \
        getattr(isystem, 'longitude', None)
    ctx.instance.runtime_properties['distributed_cloud_role'] = \
        isystem.distributed_cloud_role

    ihosts = ctx.instance.runtime_properties.get('ihosts')
    for ihost in isystem.ihosts:
        if ihost.uuid not in ihosts:
            ihosts[ihost.uuid] = {
                'hostname': ihost.hostname,
                'mgmt_ip': ihost.mgmt_ip,
                'id': ihost.id,
                'personality': ihost.personality,
                'subfunctions': ihost.subfunctions,
            }
    ctx.instance.runtime_properties['ihosts'] = ihosts
