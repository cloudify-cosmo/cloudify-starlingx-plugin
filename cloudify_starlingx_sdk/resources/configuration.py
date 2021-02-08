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
from cgtsclient.client import get_client


class ConfigurationResource(StarlingXResource):
    """Base class for objects that use the cgtsclient."""

    @property
    def connection(self):
        return get_client(**self.client_config)

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()


class ISystemResource(ConfigurationResource):
    """Class representing Starlingx I-system or "controller" objects."""

    def list(self):
        return self.connection.isystem.list()

    def get(self):
        return self.connection.isystem.get(self.resource_id)

    @property
    def ihosts(self):
        ihosts_list = []
        for ihost in self.connection.ihost.list():
            if ihost.system_uuid != self.resource_id:
                continue
            ihosts_list.append(ihost)
        return ihosts_list

    @property
    def region_name(self):
        return self.resource.region_name

    def to_dict(self):
        return {
            'name': self.resource.name,
            'description': self.resource.description,
            'location': self.resource.location,
            'system_type': self.resource.system_type,
            'system_mode': self.resource.system_mode,
            'region_name': self.region_name,
            'latitude': getattr(self.resource, 'latitude', None),
            'longitude': getattr(resource, 'latitude', None),
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
