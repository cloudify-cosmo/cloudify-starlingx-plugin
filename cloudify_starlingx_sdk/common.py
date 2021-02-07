# #######
# copyright (c) 2021 Cloudify Platform Ltd. All rights reserved
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


class InvalidINSecureValue(Exception):
    pass


class StarlingXResource(object):
    # Taken from Cloudify Openstack Plugin v3, because they are basically
    # the same API base. Maybe we will merge plugins later.
    service_type = None
    resource_type = None

    id_key = 'uuid'
    name_key = 'name'

    def __init__(self, client_config, resource_config=None, logger=None):
        self.client_config = client_config
        self.logger = logger
        self.config = resource_config or {}
        self.resource_id = self.get_identifier()
        self.name = self.config.get(self.name_key)
        self._resource = None

    @property
    def connection(self):
        raise NotImplementedError()

    @property
    def auth_url(self):
        return self.client_config.get('auth_url')

    @property
    def domain_auth_sets(self):
        return [
            {'user_domain_id', 'project_domain_id'},
            {'user_domain_name', 'project_domain_name'},
            {'user_domain_id', 'project_domain_name'},
            {'user_domain_name', 'project_domain_id'},
        ]

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()

    def get_identifier(self):
        return self.config.get(self.id_key,
                               self.config.get(self.name_key))

    @property
    def resource(self):
        if not self._resource:
            self._resource = self.get()
        return self._resource
