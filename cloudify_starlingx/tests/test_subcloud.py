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

from cloudify.constants import NODE_INSTANCE

from unittest.mock import patch
from . import StarlingXTestBase
from ..resources.subcloud import poststart


class StarlingXSubcloudTest(StarlingXTestBase):

    @patch('cloudify_starlingx_sdk.resources.distributed_cloud.client')
    @patch('cloudify_starlingx_sdk.resources.configuration.get_client')
    def test_poststart(self, _, __):
        ctx = self.get_mock_ctx(reltype=NODE_INSTANCE)
        poststart(ctx=ctx)
        self.assertIn('subcloud', ctx.instance.runtime_properties.keys())
