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

from cloudify.constants import NODE_INSTANCE, RELATIONSHIP_INSTANCE

from unittest.mock import patch
from . import StarlingXTestBase
from ..resources.subcloud import poststart, preconfigure


class StarlingXSubcloudTest(StarlingXTestBase):

    def test_preconfigure(self):
        ctx = self.get_mock_ctx(reltype=RELATIONSHIP_INSTANCE)
        preconfigure(None, ctx=ctx)
        self.assertEqual(
            ctx.source.instance.runtime_properties['controller_region_name'],
            'taco')

    @patch('cloudify_starlingx_sdk.resources.distributed_cloud.client')
    def test_poststart(self, _):
        ctx = self.get_mock_ctx(reltype=NODE_INSTANCE)
        ctx.instance.runtime_properties['controller_region_name'] = 'ball'
        poststart(ctx=ctx)
        expected = {
            'external_id',
            'name',
            'location',
            'description',
            'group_id',
            'oam_floating_ip',
            'management_state'}
        self.assertTrue(
            expected.issubset(set(ctx.instance.runtime_properties.keys())))
