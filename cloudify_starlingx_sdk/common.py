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

from re import search
from copy import deepcopy
from ipaddress import ip_address, IPv4Address
from urllib.parse import urlparse, urlunparse


def is_ipv4(ip):
    return True if type(ip_address(ip)) is IPv4Address else False


def cleanup_netloc(netloc):
    if netloc.endswith(':25000'):
        result = search('(.*):25000', netloc)
        ip = result.group(1)
        port = '25000'
    elif netloc.endswith(':5000'):
        result = search('(.*):5000', netloc)
        ip = result.group(1)
        port = '5000'
    else:
        return netloc

    try:
        if is_ipv4(ip):
            return netloc
        return '[{ip}]:{port}'.format(ip=ip, port=port)
    except ValueError:
        return netloc


def cleanup_auth_url(auth_url):
    """ There are a few particular variations to this URL.

    :param auth_url:
    :return:
    """
    # http or https, a hostname, or IPv4/IPv6 IP, v3 or v2.0
    scheme, netloc, path, _, __, ___ = urlparse(auth_url)

    # Sometimes, urlparse read netloc into the path
    if path and not netloc:
        netloc = path
        if '/v3' in netloc:
            netloc.replace('/v3', '')
        path = ''
        if '/v2.0' in netloc:
            netloc.replace('/v2.0', '')
            path = 'v2.0'

    # If not path default to v3.
    if not path:
        path = 'v3'
    # Verify that we have the correct port.
    if netloc.endswith(':25000'):
        pass
    elif not netloc.endswith(':5000'):
        netloc = netloc + ':5000'

    # Make sure that we have a scheme
    if not scheme:
        scheme = 'https'
    elif scheme not in ['http', 'https']:
        netloc = scheme + ':' + netloc
        scheme = 'https'

    netloc = cleanup_netloc(netloc)

    return urlunparse((scheme, netloc, path, '', '', ''))


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
        self.logger.info('config {}'.format(self.client_config))

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
            # Make sure that we are sending a useful URL.
            config[key] = cleanup_auth_url(config[key])
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
