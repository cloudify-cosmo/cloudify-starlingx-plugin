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

import requests


class StarlingXException(Exception):
    pass


class InvalidINSecureValue(Exception):
    pass


class StarlingXFatalException(Exception):
    def __init__(self, message):
        self.message = message


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

    @staticmethod
    def cleanup_config(config):
        return deepcopy(config)

    def merge_configs(self, config):
        kwargs = config.pop('kwargs', {})
        config.update(kwargs)
        os_kwargs = config.pop('os_kwargs', {})
        config.update(os_kwargs)

        # Clean up the auth URL. Add port if necessary. Endpoint version. etc.
        for key in ['os_auth_url', 'auth_url']:
            if key not in config:
                continue
            # Check that https is used appropriately.
            if not ('insecure' in config or
                    'cacert' in config or
                    'ca_file' in config or
                    'os_cacert' in config) and \
                    'https' in config[key]:
                config[key] = config[key].replace('https', 'http')
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


class StarlingxPatchClient(object):
    AVAILABLE_VERSION = 'v1'

    @classmethod
    def get_for_mock_server(cls):
        """
        This method will instantiate StarlingX client for Mock testing.
        """

        username = ""
        password = ""
        url = "http://localhost:8080"

        headers = {
        }

        return cls(username=username, password=password, url=url, headers=headers)

    def __init__(self, username: str, password: str, url: str, headers: dict):
        self.connection = None
        self.username = username
        self.password = password
        self.url = url
        self.headers = headers

    def get_api_version(self) -> str:
        """
        This method returns information about supported version

        :rtype: str
        """

        r = requests.get(url=self.url, headers=self.headers)

        data = r.json()

        return data

    def get_list_of_patches(self) -> list:
        """
        This method returns list of available patches.

        :rtype: list
        """

        endpoint = "{}/{}/query".format(self.url, self.AVAILABLE_VERSION)
        r = requests.get(url=endpoint, headers=self.headers)

        data = r.json()

        return data

    def get_patch_details(self, patch_id: str) -> dict:
        """
        This method returns detailed information about given patch id.
        """

        endpoint = "{}/{}/show/{}".format(self.url, self.AVAILABLE_VERSION, patch_id)

        r = requests.get(url=endpoint, headers=self.headers)

        data = r.json()

        return data
