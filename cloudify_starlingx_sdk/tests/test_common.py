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

from ..common import StarlingXResource


class StarlingXCommonBase(unittest.TestCase):

    def setUp(self):
        super(StarlingXCommonBase, self).setUp()


class StarlingXResourceTest(StarlingXCommonBase):

    def test_starlingx_resource_instance(self):
        resource = StarlingXResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={
                'name': 'foo-name',
                'uuid': '00000000-0000-0000-0000-000000000000'
            },
            logger=unittest.mock.Mock()
        )

        self.assertEqual(resource.resource_id,
                         '00000000-0000-0000-0000-000000000000')
        self.assertEqual(resource.name, 'foo-name')
