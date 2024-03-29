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

from unittest.mock import patch, Mock

from .test_common import StarlingXCommonBase
from ..resources.distributed_cloud import SubcloudResource


class StarlingXDistributedCloudTest(StarlingXCommonBase):

    @patch('cloudify_starlingx_sdk.resources.distributed_cloud.client')
    def test_subcloud_resource_instance(self, client):
        client.client.subcloud_manager.list_subclouds = Mock()
        client.client.subcloud_manager.subcloud_additional_details = Mock()

        mock_client = Mock()
        subcloud_manager_mock = Mock()
        subcloud_manager_mock.list_subclouds = Mock()
        subcloud_manager_mock.subcloud_additional_details = Mock()
        mock_client.subcloud_manager.return_value = subcloud_manager_mock

        resource = SubcloudResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={
                'name': 'foo-name',
            },
            logger=Mock()
        )

        self.assertEqual(resource.resource_id,
                         'foo-name')
        self.assertEqual(resource.name, 'foo-name')
        self.assertIsNotNone(resource.get())
        self.assertIsNotNone(resource.list())
