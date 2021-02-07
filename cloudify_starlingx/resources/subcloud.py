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
    """ Populate the subcloud resource with relevant data.

    :param resource:
    :param ctx:
    :return:
    """
    resource.client_config['region_name'] = \
        ctx.instance.runtime_properties['controller_region_name']
    subcloud = resource.get()
    ctx.instance.runtime_properties.update(subcloud.to_dict())
    ctx.instance.update()
