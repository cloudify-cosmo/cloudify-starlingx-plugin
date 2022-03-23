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

import os
from copy import deepcopy

from ..common import (StarlingXResource, StarlingXException)

from keystoneauth1 import session
from keystoneauth1.identity import v3

from dcmanagerclient.api import client
from dcmanagerclient.exceptions import APIException
from dcmanagerclient.api.v1 import client as client_v1
from keystoneauth1.exceptions.catalog import EndpointNotFound


class DistributedCloudResource(StarlingXResource):

    @staticmethod
    def cleanup_config(config):
        creds = deepcopy(config)
        for key, val in list(creds.items()):
            if key.startswith('os_'):
                creds[key.split('os_')[1]] = creds.pop(key)
            if 'ca_file' in creds:
                creds['cacert'] = creds.pop('ca_file')
            if 'password' in creds:
                creds['api_key'] = creds.pop('password')
        if 'api_version' in creds:
            del creds['api_version']
        return creds

    @property
    def connection(self):
        if not self._connection:
            cacert = self.client_config.get('cacert')
            insecure = self.client_config.get(
                'insecure', False)
            if cacert or insecure:
                if cacert:
                    os.environ["REQUESTS_CA_BUNDLE"] = cacert
                auth_dict = dict(
                    auth_url=self.client_config.get('auth_url'),
                    username=self.client_config.get('username'),
                    password=self.client_config.get('api_key'),
                    project_name=self.client_config.get('project_name'),
                    user_domain_name=self.client_config.get(
                        'user_domain_name'),
                    project_domain_name=self.client_config.get(
                        'project_domain_name'),
                )
                auth = v3.Password(**auth_dict)
                sess = session.Session(
                    auth=auth, verify=cacert if not insecure else False)
                self._connection = client_v1.Client(
                    session=sess,
                    insecure=insecure)
            else:
                self._connection = client.client(**self.client_config)
        return self._connection

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()


class SubcloudResource(DistributedCloudResource):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subcloud_detail = None
        self._subcloud_group_detail = None

    id_key = 'subcloud_id'

    def list(self):
        return self.connection.subcloud_manager.list_subclouds()

    def get(self, name=None):
        name = name or self.resource_id
        return self._get(name)

    def _get(self, resource_id=None):
        resource_id = resource_id or self.resource_id
        if resource_id == self.resource_id:
            return self.subcloud_detail
        return self._get_detail(resource_id)

        # try:
        #     # result = self.connection.subcloud_manager.subcloud_detail(
        #     #     resource_id)
        #     return self._get_detail(resource_id)
        # except EndpointNotFound:
        #     return None
        # I am not sure why they return a list here.
        # if len(result) == 1:
        #     return result[0]
        # return result

    @property
    def subcloud_detail(self):
        if not self._subcloud_detail:
            self._subcloud_detail = self.get_detail()
        return self._subcloud_detail

    def _get_detail(self, name=None):
        name = name or self.resource_id
        try:
            result = \
                self.connection.subcloud_manager.subcloud_additional_details(
                    name)
        except EndpointNotFound:
            return
        # I am not sure why they return a list here.
        if len(result) == 1:
            return result[0]
        return result

    def get_detail(self):
        try:
            return self._get_detail()
        except APIException as e:
            raise StarlingXException(e)

    @property
    def oam_floating_ip(self):
        return self.subcloud_detail.oam_floating_ip

    def get_oam_floating_ip(self, name):
        resource = self._get_detail(name)
        return resource.oam_floating_ip

    def to_dict(self):
        return self.get_subcloud_as_dict(self.resource)

    @property
    def subcloud_group_detail(self):
        if not self._subcloud_group_detail:
            self._subcloud_group_detail = self.get_subcloud_group()
        return self._subcloud_group_detail

    def get_subcloud_group(self, group_id=None):
        group_id = group_id or self.resource.group_id
        # TODO: We should only need to call this one time.
        try:
            result = self.connection.subcloud_group_manager.\
                subcloud_group_detail(group_id)
        except EndpointNotFound:
            return None
        # I am not sure why they return a list here.
        if len(result) == 1:
            return result[0]
        return result

    def get_subcloud_group_name(self, group_id):
        if group_id == self.resource.group_id:
            return self.subcloud_group_detail.name
        subcloud_group = self.get_subcloud_group(group_id)
        if subcloud_group:
            return subcloud_group.name

    def get_subcloud_as_dict(self, resource):
        return {
            str(resource.subcloud_id): {
                'external_id': str(resource.subcloud_id),
                'name': resource.name,
                'description': resource.description,
                'location': str(resource.location).lower(),
                'group_id': resource.group_id,
                'group_name': self.get_subcloud_group_name(resource.group_id),
                'oam_floating_ip': self.get_oam_floating_ip(resource.name),
                'management_state': resource.management_state
            }
        }

    def get_subcloud_from_name(self, name):
        return self._get(name)
