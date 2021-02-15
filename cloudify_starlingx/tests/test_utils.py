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

from cloudify.exceptions import NonRecoverableError
from cloudify.constants import RELATIONSHIP_INSTANCE

from . import StarlingXTestBase
from ..utils import resolve_ctx, resolve_node_ctx_from_relationship


class StarlingXUtilsTest(StarlingXTestBase):

    def test_resolve_node_ctx_from_relationship(self):
        ctx = self.get_mock_ctx('baz', reltype=RELATIONSHIP_INSTANCE)
        with self.assertRaises(NonRecoverableError):
            resolve_node_ctx_from_relationship(ctx)
        ctx = self.get_mock_ctx(reltype=RELATIONSHIP_INSTANCE)
        self.assertIs(ctx.source, resolve_node_ctx_from_relationship(ctx))
        self.assertIsNot(ctx.target, resolve_node_ctx_from_relationship(ctx))

    def test_resolve_ctx(self):
        ctx = self.get_mock_ctx()
        ctx2 = self.get_mock_ctx(reltype=RELATIONSHIP_INSTANCE)
        self.assertIs(ctx, resolve_ctx(ctx))
        self.assertIsNot(ctx, resolve_ctx(ctx2))
