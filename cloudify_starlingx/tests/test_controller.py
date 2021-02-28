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

from unittest.mock import patch

from cloudify.constants import NODE_INSTANCE
from cloudify.exceptions import NonRecoverableError

from . import StarlingXTestBase
from ..resources.controller import poststart


class StarlingXControllerTest(StarlingXTestBase):

    @patch('cloudify_starlingx_sdk.resources.configuration.get_client')
    @patch('cloudify_starlingx_sdk.resources.distributed_cloud.client')
    def test_poststart(self, _, __):
        ctx = self.get_mock_ctx(reltype=NODE_INSTANCE)
        ctx.node.properties['resource_config'] = {
            'uuid': 'foo',
            'name': 'bar',
            'distributed_cloud_role': 'foo',
            'system_type': 'All-in-one',
            'system_mode': 'duplex'
        }
        # Test that an invalid configuration raises an error.
        self.assertRaises(NonRecoverableError, poststart, ctx=ctx)
        ctx.node.properties['resource_config'] = {
            'uuid': 'foo',
            'name': 'bar',
            'distributed_cloud_role': 'Subcloud',
            'system_type': 'Standard',
            'system_mode': 'simplex'
        }
        # Test that everything goes smoothly with a valid configuration.
        with patch('cloudify_starlingx_sdk.'
                   'resources.configuration.'
                   'SystemResource.is_subcloud', return_value=True):
            poststart(ctx=ctx)
        expected = {
            'name',
            'location',
            'description',
            'system_type',
            'system_mode',
            'region_name',
            'latitude',
            'longitude',
            'distributed_cloud_role'}
        self.assertTrue(
            expected.issubset(
                set(
                    ctx.instance.runtime_properties['resource_config'].keys()
                )
            )
        )
