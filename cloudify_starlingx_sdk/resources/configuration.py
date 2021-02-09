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

from cgtsclient.client import get_client

from ..common import StarlingXResource
from .distributed_cloud import SubcloudResource


class ConfigurationResource(StarlingXResource):
    """Base class for objects that use the cgtsclient."""

    def __init__(self, *args, **kwargs):
        kwargs['client_config'] = self.convert_client_config_to_cgts(
            kwargs.get('client_config'))
        super().__init__(*args, **kwargs)

    @property
    def connection(self):
        return get_client(**self.client_config)

    @staticmethod
    def convert_client_config_to_cgts(client_args):
        os_client_args = {}
        for key, val in client_args.items():
            os_client_args['os_{key}'.format(key=key)] = val
        os_client_args['os_password'] = os_client_args.pop('os_api_key')
        os_client_args['api_version'] = 1
        return os_client_args

    @staticmethod
    def convert_client_config_to_distcloud(client_args):
        ds_client_args = {}
        for key, val in client_args.items():
            ds_client_args[key.replace('os_', '')] = val
        ds_client_args['api_key'] = ds_client_args.pop('password')
        del ds_client_args['api_version']
        return ds_client_args

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()


class ISystemResource(ConfigurationResource):
    """Class representing Starlingx I-system or "controller" objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subcloud_resource = None

    def list(self):
        return self.connection.isystem.list()

    def get(self):
        return self.connection.isystem.get(self.resource_id)

    @property
    def ihosts(self):
        ihosts_list = []
        for ihost in self.connection.ihost.list():
            if ihost.system_uuid == self.resource_id:
                ihosts_list.append(ihost)
        return ihosts_list

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
        if not self._subcloud_resource:
            self._subcloud_resource = SubcloudResource(
                client_config=self.convert_client_config_to_distcloud(
                    self.client_config),
                resource_config=self.config)
        return self._subcloud_resource

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


class IhostResource(ConfigurationResource):

    def list(self):
        return self.connection.ihost.list()

    def get(self):
        return self.connection.ihost.get(self.resource_id)
