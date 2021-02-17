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

from unittest.mock import patch, MagicMock

from ..workflows import discover
from ..workflows.utils import CONTROLLER_TYPE
from . import StarlingXTestBase


class StarlingXWorkflowTest(StarlingXTestBase):

    def get_mock_rest_client(self):
        mock_node = MagicMock(node_id='foo',
                              type_hierarchy=CONTROLLER_TYPE)
        mock_node.id = mock_node.node_id
        mock_node.properties = {
            'client_config': {
                'api_key': 'foo',
            },
            'resource_config': {
                'uuid': 'foo',
                'name': 'foo'
            }
        }
        nodes_list = [mock_node]
        mock_nodes_client = MagicMock()
        mock_nodes_client.list = MagicMock(return_value=nodes_list)
        mock_instance = MagicMock()
        mock_instance.node = mock_node
        mock_instance.node_id = mock_node.node_id
        mock_instance.runtime_properties = {
            'external_id': 'foo',
            'name': 'foo',
        }
        instances_list = [mock_instance]
        mock_instances_client = MagicMock()
        mock_instances_client.list = MagicMock(return_value=instances_list)
        mock_deployments_client = MagicMock()
        mock_deployments_client.create = MagicMock()
        mock_rest_client = MagicMock()
        mock_rest_client.nodes = mock_nodes_client
        mock_rest_client.node_instances = mock_instances_client
        mock_rest_client.deployments = mock_deployments_client
        return mock_rest_client

    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    @patch('cloudify_starlingx_sdk.resources.distributed_cloud.client')
    @patch('cloudify_starlingx_sdk.resources.configuration.get_client')
    def test_discover_subclouds(self, _, __, get_rest_client):
        ctx = self.get_mock_ctx('foo', reltype=NODE_INSTANCE)
        discover.discover_subclouds(node_id='foo', ctx=ctx)
        ctx.get_node.assert_called()

        mock_rest_client = self.get_mock_rest_client()
        get_rest_client.return_value = mock_rest_client
        ctx = self.get_mock_ctx('foo', reltype=NODE_INSTANCE)
        discover.discover_subclouds(ctx=ctx)
        assert mock_rest_client.nodes.list.called
        assert mock_rest_client.node_instances.list.called

    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    @patch('cloudify_starlingx_sdk.resources.distributed_cloud.client')
    @patch('cloudify_starlingx_sdk.resources.configuration.get_client')
    def test_discover_and_deploy(self, _, __, get_rest_client):
        mock_rest_client = self.get_mock_rest_client()
        get_rest_client.return_value = mock_rest_client
        ctx = self.get_mock_ctx('foo', reltype=NODE_INSTANCE)
        ctx.instance.runtime_properties['subclouds'] = {
            'subcloud1': {
                'external_id': 'taco',
                'name': 'bell',
                'oam_floating_ip': 'baz'
            }
        }
        discover.discover_and_deploy('bar', node_id='foo', ctx=ctx)
        assert mock_rest_client.deployments.create.called
