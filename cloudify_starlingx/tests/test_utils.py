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
from cloudify.constants import RELATIONSHIP_INSTANCE

from .. import utils
from . import StarlingXTestBase


class StarlingXUtilsTest(StarlingXTestBase):

    def test_resolve_node_ctx_from_relationship(self):
        ctx = self.get_mock_ctx('baz', reltype=RELATIONSHIP_INSTANCE)
        with self.assertRaises(NonRecoverableError):
            utils.resolve_node_ctx_from_relationship(ctx)
        ctx = self.get_mock_ctx(reltype=RELATIONSHIP_INSTANCE)
        self.assertIs(ctx.source,
                      utils.resolve_node_ctx_from_relationship(ctx))
        self.assertIsNot(ctx.target,
                         utils.resolve_node_ctx_from_relationship(ctx))

    def test_resolve_ctx(self):
        ctx = self.get_mock_ctx()
        ctx2 = self.get_mock_ctx(reltype=RELATIONSHIP_INSTANCE)
        self.assertIs(ctx, utils.resolve_ctx(ctx))
        self.assertIsNot(ctx, utils.resolve_ctx(ctx2))

    def test_update_prop_resource(self):
        r = Mock()
        to_dict = {'baz': 'baz', 'bar': 'bar'}
        r.to_dict.return_value = to_dict
        ctx = self.get_mock_ctx('foo')
        utils.update_prop_resource(ctx.instance, r, 'foo')
        assert 'foo' in ctx.instance.runtime_properties
        assert ctx.instance.runtime_properties['foo'] == to_dict
        del ctx.instance.runtime_properties['foo']
        utils.update_prop_resources(ctx.instance, [r], 'foo')
        assert 'foo' in ctx.instance.runtime_properties
        assert ctx.instance.runtime_properties['foo'] == to_dict

    def test_kubernetes_openstack_props(self):
        k = Mock()
        k.resource = Mock(
            cluster_api_endpoint='foo',
            admin_token='bar',
            cluster_ca_cert='baz',
            value='bar')
        ctx = self.get_mock_ctx('foo')
        utils.update_kubernetes_props(ctx.instance, [k])
        assert ctx.instance.runtime_properties['k8s_ip'] == 'foo'
        assert \
            ctx.instance.runtime_properties['k8s_service_account_token'] == \
            'bar'
        assert ctx.instance.runtime_properties['k8s_cert'] == 'baz'
        utils.update_openstack_props(ctx.instance,
                                     [k],
                                     ctx.node.properties['client_config'])
        assert ctx.instance.runtime_properties['openstack_ip'] == 'bar'
        assert ctx.instance.runtime_properties['openstack_key'] == 'bar'

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_with_rest_client(self, _):
        @utils.with_rest_client
        def mock_function(**kwargs):
            return kwargs
        self.assertIn('rest_client', mock_function())

    @patch('cloudify_starlingx.utils.wtx')
    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_get_instances_of_nodes(self, mock_client, mock_ctx):
        self.assertRaises(NonRecoverableError, utils.get_instances_of_nodes)
        utils.get_instances_of_nodes('foo')
        mock_ctx.get_node.assert_called_with('foo')
        utils.get_instances_of_nodes(node_type='foo', deployment_id='bar')
        assert call().nodes.list(deployment_id='bar') in mock_client.mock_calls

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_get_node_instances_by_type(self, mock_client):
        result = utils.get_node_instances_by_type(
            node_type='foo', deployment_id='bar')
        assert call().nodes.list(deployment_id='bar') in mock_client.mock_calls
        self.assertIsInstance(result, list)

    @patch('cloudify_starlingx.utils.get_rest_client')
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

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_resolve_intrinsic_functions(self, mock_client):
        expected = 'foo'
        result = utils.resolve_intrinsic_functions(expected)
        assert expected == result
        prop = {'get_secret': 'bar'}
        utils.resolve_intrinsic_functions(prop)
        assert call().secrets.get('bar') in mock_client.mock_calls

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_get_secret(self, mock_client):
        prop = 'bar'
        utils.get_secret(secret_name=prop)
        assert call().secrets.get('bar') in mock_client.mock_calls

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_create_deployment(self, mock_client):
        prop = {
            'inputs': {'baz': 'taco'},
            'blueprint_id': 'foo',
            'deployment_id': 'bar',
            'labels': [{'foo': 'bar'}]
        }
        utils.create_deployment(**prop)
        assert call().deployments.create(
            'foo',
            'bar',
            {'baz': 'taco'},
            labels=[{'foo': 'bar'}]
        ) in mock_client.mock_calls

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_get_deployment_labels(self, _):
        assert isinstance(utils.get_deployment_labels('foo'), dict)
        assert utils.get_deployment_label_by_name('foo', 'foo') is None

    def test_convert_list_dict(self):
        my_list = [{'key': 'foo', 'value': 'bar'}]
        my_dict = {'foo': 'bar'}
        assert utils.convert_list_to_dict(my_list) == my_dict
        assert utils.convert_dict_to_list(my_dict) == [my_dict]

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_get_site(self, mock_client):
        prop = 'bar'
        utils.get_site(site_name=prop)
        assert call().sites.get(prop) in mock_client.mock_calls

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_create_site(self, mock_client):
        prop = {
            'site_name': 'foo',
            'location': 'bar,baz'
        }
        utils.create_site(**prop)
        assert call().sites.create(
            'foo',
            'bar,baz'
        ) in mock_client.mock_calls

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_update_site(self, mock_client):
        prop = {
            'site_name': 'foo',
            'location': 'bar,baz'
        }
        utils.update_site(**prop)
        assert call().sites.update(
            'foo',
            'bar,baz'
        ) in mock_client.mock_calls

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_update_deployment_site(self, mock_client):
        prop = {
            'deployment_id': 'foo',
            'site_name': 'bar,baz'
        }
        utils.update_deployment_site(**prop)
        assert call().deployments.get(
            deployment_id='foo') in mock_client.mock_calls
        assert call().deployments.set_site(
            'foo',
            detach_site=True
        ) in mock_client.mock_calls

    @patch('cloudify_starlingx.utils.get_rest_client')
    def test_assign_site(self, mock_client):
        prop = {
            'deployment_id': 'foo',
            'location': 'bar,baz'
        }
        utils.assign_site(**prop)
        assert call().deployments.get(
            deployment_id='foo') in mock_client.mock_calls
        assert call().deployments.set_site(
            'foo',
            detach_site=True
        ) in mock_client.mock_calls
