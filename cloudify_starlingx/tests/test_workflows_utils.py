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

from unittest.mock import patch, call, Mock

from cloudify.exceptions import NonRecoverableError

from ..workflows import utils
from . import StarlingXTestBase


class StarlingXWorkflowTest(StarlingXTestBase):

    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    def test_with_rest_client(self, _):
        @utils.with_rest_client
        def mock_function(**kwargs):
            return kwargs
        self.assertIn('rest_client', mock_function())

    @patch('cloudify_starlingx.workflows.utils.wtx')
    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    def test_get_instances_of_nodes(self, mock_client, mock_ctx):
        self.assertRaises(NonRecoverableError, utils.get_instances_of_nodes)
        utils.get_instances_of_nodes('foo')
        mock_ctx.get_node.assert_called_with('foo')
        utils.get_instances_of_nodes(node_type='foo', deployment_id='bar')
        assert call().nodes.list(deployment_id='bar') in mock_client.mock_calls

    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    def test_get_node_instances_by_type(self, mock_client):
        result = utils.get_node_instances_by_type(
            node_type='foo', deployment_id='bar')
        assert call().nodes.list(deployment_id='bar') in mock_client.mock_calls
        self.assertIsInstance(result, list)

    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    def update_runtime_properties(self, mock_client):
        instance = Mock(id='foo', state=0)
        instance.runtime_properties = {'foo': 'taco'}
        resource = Mock(resource_id='bar')
        resource.to_dict.return_value = {'foo': 'bar'}
        resources = [resource]
        utils.update_runtime_properties(
            instance=instance, resources=resources, prop_name='foo')
        assert call().nodeinstances.update(
            'id',
            'bar',
            {'foo': 'taco', resource.resource_id: resource.to_dict()},
            1) in mock_client.mock_calls

    def test_desecretize_client_config(self):
        expected = {'foo': 'bar'}
        result = utils.desecretize_client_config(expected)
        assert expected == result

    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    def test_check_for_secret_value(self, mock_client):
        expected = 'foo'
        result = utils.check_for_secret_value(expected)
        assert expected == result
        prop = {'get_secret': 'bar'}
        utils.check_for_secret_value(prop)
        assert call().secrets.get('bar') in mock_client.mock_calls

    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    def test_get_secret(self, mock_client):
        prop = 'bar'
        utils.get_secret(secret_name=prop)
        assert call().secrets.get('bar') in mock_client.mock_calls

    @patch('cloudify_starlingx.workflows.utils.get_rest_client')
    def test_create_deployment(self, mock_client):
        prop = {
            'inputs': {'baz': 'taco'},
            'blueprint_id': 'foo',
            'deployment_id': 'bar',
        }
        utils.create_deployment(**prop)
        assert call().deployments.create(
            'foo',
            'bar',
            {'baz': 'taco'}) in mock_client.mock_calls
