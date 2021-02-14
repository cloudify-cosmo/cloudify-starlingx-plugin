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
from ..utils import update_prop_resource, update_prop_resources
from cloudify_starlingx_sdk.resources.configuration import SystemResource


@with_starlingx_resource(SystemResource)
def poststart(resource, ctx):
    """ Populate the subcloud resource with relevant data.

    :param resource:
    :param ctx:
    :return:
    """

    update_prop_resource(ctx.instance, resource)
    update_prop_resources(ctx.instance, resource.host_resources, 'hosts')
    update_prop_resource(ctx.instance, resource.subcloud_resource, 'subcloud')
