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


from copy import deepcopy


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
        self.logger = logger
        self.client_config = self.merge_configs(client_config)
        self.config = resource_config or {}
        self.resource_id = self.get_identifier()
        self.name = self.config.get(self.name_key)
        self._resource = None
        self._connection = None

    @property
    def connection(self):
        raise NotImplementedError()

    @property
    def auth_url(self):
        return self.client_config.get('auth_url')

    def cleanup_auth_url(self, auth_url):
        if not auth_url.startswith('http://') and not \
                auth_url.startswith('https://'):
            auth_url = 'http://{u}'.format(u=auth_url)
        if auth_url.endswith('/'):
            auth_url.strip('/')
        if not auth_url.endswith(':5000/v3'):
            auth_url = '{u}:5000/v3'.format(u=auth_url)
        return auth_url

    @staticmethod
    def cleanup_config(config):
        return deepcopy(config)

    def merge_configs(self, config):
        kwargs = config.pop('kwargs', {})
        config.update(kwargs)
        os_kwargs = config.pop('os_kwargs', {})
        config.update(os_kwargs)
        for key in ['os_auth_url', 'auth_url']:
            if key in config:
                config[key] = self.cleanup_auth_url(config[key])
        return self.cleanup_config(config)

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
