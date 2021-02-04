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
from cloudify_starlingx_sdk.resources.configuration import ApplicationResource


@with_starlingx_resource(ApplicationResource)
def poststart(resource, ctx):
    app = resource.get()
    ctx.instance.runtime_properties['external_id'] = app.resource_id
    ctx.instance.runtime_properties['name'] = app.name
    ctx.instance.runtime_properties['app_version'] = app.app_version
    ctx.instance.runtime_properties['manifest_name'] = app.manifest_name
    ctx.instance.runtime_properties['manifest_file'] = app.manifest_file
    ctx.instance.update()
