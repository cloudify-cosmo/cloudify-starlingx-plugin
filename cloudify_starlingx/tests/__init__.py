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

import unittest
from cloudify.constants import NODE_INSTANCE


class StarlingXTestBase(unittest.TestCase):

    def setUp(self):
        super(StarlingXTestBase, self).setUp()

    def get_mock_ctx(self, node_name='foo', reltype=NODE_INSTANCE):
        ctx = unittest.mock.MagicMock()

        ctx.type = reltype

        node = unittest.mock.MagicMock()
        node.properties = {
            'client_config': {
                'api_version': 'v1',
                'username': 'foo',
                'api_key': 'bar',
                'auth_url': 'baz',
                'region_name': 'taco'
            },
            'resource_config': {}
        }
        ctx.node = node
        instance = unittest.mock.MagicMock()
        instance.runtime_properties = {
            'resource_config': {
                'distributed_cloud_role': 'systemcontroller'
            }
        }
        instance.node_id = node_name
        ctx.instance = instance
        ctx._context = {'node_id': node_name}
        ctx.node.id = node_name

        source = unittest.mock.MagicMock()
        target = unittest.mock.MagicMock()
        source._context = {'node_id': 'foo'}
        target._context = {'node_id': 'bar'}
        source.instance = instance
        source.node = node
        target.node = node
        target.instance = instance
        ctx.source = source
        ctx.target = target
        ctx.node.instances = [ctx.instance]
        ctx.get_node = unittest.mock.MagicMock(return_value=ctx.node)
        ctx.deployment.id = 'baz'
        ctx.blueprint.id = 'baz'

        return ctx
