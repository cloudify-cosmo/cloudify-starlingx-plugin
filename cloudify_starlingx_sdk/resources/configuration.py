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

from copy import deepcopy

from cgtsclient.client import get_client

from ..common import StarlingXResource
from .distributed_cloud import SubcloudResource


class ConfigurationResource(StarlingXResource):
    """Base class for objects that use the cgtsclient."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def connection(self):
        creds = deepcopy(self.client_config)
        for key, val in list(creds.items()):
            if not key.startswith('os_'):
                creds['os_{key}'.format(key=key)] = val
        if 'os_api_key' in creds:
            creds['os_password'] = creds.pop('os_api_key')
        creds['api_version'] = 1
        return get_client(**creds)

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()


class SystemResource(ConfigurationResource):
    """Class representing Starlingx I-system or "controller" objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._host_resources = None
        self._subcloud_resource = None

    def list(self):
        return self.connection.isystem.list()

    def get(self):
        return self.connection.isystem.get(self.resource_id)

    @property
    def hosts(self):
        host_list = []
        for host in self.connection.ihost.list():
            if host.isystem_uuid == self.resource_id:
                host_list.append(host)
        return host_list

    @property
    def region_name(self):
        return self.resource.region_name

    @property
    def distributed_cloud_role(self):
        if self.resource.distributed_cloud_role.lower() == 'null':
            return
        return self.resource.distributed_cloud_role

    @property
    def system_type(self):
        return self.resource.system_type

    @property
    def system_mode(self):
        return self.resource.system_mode

    @property
    def is_standalone_system(self):
        return not self.distributed_cloud_role

    @property
    def is_system_controller(self):
        return self.distributed_cloud_role.lower() == 'systemcontroller'

    @property
    def is_subcloud(self):
        return self.distributed_cloud_role.lower() == 'subcloud'

    @property
    def subcloud_resource(self):
        # If self.is_subcloud() is True, then we will need this
        # in order to populate runtime properties.
        if not self._subcloud_resource:
            self._subcloud_resource = SubcloudResource(
                client_config=self.client_config,
                resource_config=self.config,
                logger=self.logger
            )
        return self._subcloud_resource.get_subcloud_from_name(
            self.resource.name)

    @property
    def host_resources(self):
        host_resources = []
        if not self._host_resources:
            for host in self.hosts:
                host_resources.append(
                    HostResource(client_config=self.client_config,
                                 resource_config={'uuid': host.uuid},
                                 logger=self.logger))
            self._host_resources = host_resources
        return self._host_resources

    @property
    def oam_floating_ip(self):
        return self.subcloud_resource.oam_floating_ip

    def to_dict(self):
        return {
            'name': self.resource.name,
            'description': self.resource.description,
            'location': self.resource.location,
            'system_type': self.resource.system_type,
            'system_mode': self.resource.system_mode,
            'region_name': self.region_name,
            'latitude': getattr(self.resource, 'latitude', None),
            'longitude': getattr(self.resource, 'latitude', None),
            'distributed_cloud_role': self.resource.distributed_cloud_role
        }


class ApplicationResource(ConfigurationResource):

    id_key = 'name'

    def list(self):
        return self.connection.app.list()

    def get(self):
        return self.connection.app.get(self.resource_id)

    def to_dict(self):
        return {
            'name': self.resource.name,
            'app_version': self.resource.app_version,
            'manifest_name': self.resource.manifest_name,
            'manifest_file': self.resource.manifest_file,
        }


class HostResource(ConfigurationResource):

    def list(self):
        return self.connection.ihost.list()

    def get(self):
        return self.connection.ihost.get(self.resource_id)

    def to_dict(self):
        return {
            self.resource.uuid: {
                'hostname': self.resource.hostname,
                'personality': self.resource.personality,
                'capabilities': self.resource.capabilities,
                'subfunctions': self.resource.subfunctions
            }
        }
