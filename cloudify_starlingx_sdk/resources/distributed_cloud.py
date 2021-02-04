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

from ..common import StarlingXResource
from dcmanagerclient.api import client


class DistributedCloudResource(StarlingXResource):

    @property
    def connection(self):
        return client(**self.client_config)

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()


class SubcloudResource(DistributedCloudResource):

    id_key = 'subcloud_id'

    def list(self):
        return self.connection.subcloud_manager.list_subclouds()

    def get(self):
        result = self.connection.subcloud_manager.subcloud_detail(
            self.resource_id)
        # I am not sure why they return a list here.
        if 0 == len(result) > 1:
            return
        return result[0]
