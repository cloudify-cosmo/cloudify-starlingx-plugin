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
from keystoneauth1.exceptions.auth import AuthorizationFailure

from ..common import (StarlingXResource, StarlingXFatalException)
from .distributed_cloud import SubcloudResource

NOT_STANDALONE = ['subcloud', 'systemcontroller']
STANDALONE = ['null', None]


class ConfigurationResource(StarlingXResource):
    """Base class for objects that use the cgtsclient."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def cleanup_config(config):
        creds = deepcopy(config)
        for key, val in list(creds.items()):
            if not key.startswith('os_') and key != 'insecure':
                creds['os_{key}'.format(key=key)] = creds.pop(key)
        cafile = creds.pop('os_cacert', creds.pop('os_ca_file', None))
        if cafile:
            creds['ca_file'] = cafile
        if 'os_api_key' in creds:
            creds['os_password'] = creds.pop('os_api_key')
        if 'password' in creds:
            del creds['password']
        if 'os_api_version' in creds:
            del creds['os_api_version']
        creds['api_version'] = 1
        return creds

    @property
    def connection(self):
        creds = deepcopy(self.client_config)
        if creds.get('insecure', False) and 'ca_file' in creds:
            del creds['ca_file']
        if not self._connection:
            try:
                self._connection = get_client(**creds)
            except AuthorizationFailure as e:
                if 'sslerror' in str(e).lower():
                    raise StarlingXFatalException('SSL validation failed.')
                raise StarlingXFatalException(e)
        return self._connection

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()

    def patches_list(self):
        raise NotImplemented()


class SystemResource(ConfigurationResource):
    """Class representing Starlingx I-system or "controller" objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._host_resources = None
        self._subcloud_resource = None
        self._subcloud_resources = None
        self._subcloud_resource_names = None
        self._kube_cluster_resources = None
        self._service_parameter_resources = None

    def list(self):
        return self.connection.isystem.list()

    def get(self):
        if not self.resource_id:
            systems = self.list()
            if len(systems) == 1:
                return systems[0]
            raise Exception('No system uuid was provided and '
                            'more than one system exists in the account.')
        return self.connection.isystem.get(self.resource_id)

    def get_from_name(self, name):
        return self.connection.isystem.get(name)

    def to_dict(self):
        return {
            'external_id': self.value_from_config('uuid'),
            'name': self.value_from_config('name'),
            'description': self.value_from_config('description'),
            'location': self.value_from_config('location'),
            'system_type': self.system_type,
            'system_mode': self.system_mode,
            'region_name': self.region_name,
            'latitude': str(getattr(self.resource, 'latitude', None)).lower(),
            'longitude': str(
                getattr(self.resource, 'longitude', None)).lower(),
            'distributed_cloud_role': self.distributed_cloud_role
        }

    def value_from_config(self, name):
        if hasattr(self.resource, name):
            value = getattr(self.resource, name)
        else:
            value = self.config.get(name, 'none')
        if isinstance(value, str):
            return value.lower()
        return value

    def patches_list(self):
        pass

    @property
    def region_name(self):
        return self.resource.region_name

    @property
    def distributed_cloud_role(self):
        return self.value_from_config('distributed_cloud_role')

    @property
    def system_type(self):
        return self.value_from_config('system_type')

    @property
    def system_mode(self):
        return self.value_from_config('system_mode')

    @property
    def latitude(self):
        return self.value_from_config('latitude')

    @property
    def longitude(self):
        return self.value_from_config('longitude')

    @property
    def location(self):
        return '{lat},{lon}'.format(
            lat=self.latitude, lon=self.longitude)

    @property
    def is_standalone_system(self):
        if self.value_from_config('distributed_cloud_role') in STANDALONE:
            return True
        return False

    @property
    def is_system_controller(self):
        return self.value_from_config('distributed_cloud_role') == \
               'systemcontroller'

    @property
    def is_subcloud(self):
        return self.value_from_config('distributed_cloud_role') == \
               'subcloud'

    @property
    def subcloud_resource(self):
        if not self._subcloud_resource:
            self._subcloud_resource = SubcloudResource(
                client_config=self.client_config,
                logger=self.logger
            )
        return self._subcloud_resource

    @property
    def subclouds(self):
        """ This is a list of raw subclouds.
        """
        subclouds = []
        for subcloud in self.subcloud_resource.list():
            subclouds.append(subcloud)
        return subclouds

    @property
    def subcloud_resource_names(self):
        names = []
        if not self._subcloud_resource_names:
            # TODO: Make parallel
            # TODO: Here we have two calls per subcloud.
            for subcloud in self.subclouds:
                names.append(subcloud.name)
            self._subcloud_resource_names = names
        return self._subcloud_resource_names

    @property
    def subcloud_resources(self):
        """ This is a list of the subcloud resource objects.
        I.e. interfaces for storing properties in runtime, etc.
        """
        subcloud_resources = []
        if not self._subcloud_resources:
            # TODO: Make parallel
            # TODO: Here we have two calls per subcloud.
            for subcloud in self.subclouds:
                resource = \
                    SubcloudResource(
                        client_config=self.client_config,
                        resource_config={'subcloud_id': subcloud.subcloud_id},
                        logger=self.logger)
                if resource.resource.availability_status.lower() == 'online' \
                        and resource.resource.management_state in ['managed']:
                    # We only need to include online & managed resources in
                    # the list.
                    subcloud_resources.append(resource)
            self._subcloud_resources = subcloud_resources
        return self._subcloud_resources

    @property
    def oam_floating_ip(self):
        """ If the system is a subcloud,
        this value will expose the oam floating IP.
        """
        if self.is_subcloud:
            return self.subcloud_resource.oam_floating_ip
        else:
            return

    @property
    def hosts(self):
        """ This is a list of raw hosts.
        """
        host_list = []
        for host in self.connection.ihost.list():
            if host.isystem_uuid == self.value_from_config('uuid'):
                host_list.append(host)
        return host_list

    @property
    def host_resources(self):
        """ This is a list of the host resource objects.
        I.e. interfaces for storing properties in runtime, etc.
        """
        host_resources = []
        if not self._host_resources:
            for host in self.hosts:
                host_resources.append(
                    HostResource(client_config=self.client_config,
                                 resource_config={'uuid': host.uuid},
                                 logger=self.logger))
            # connection=self.connection))
            self._host_resources = host_resources
        return self._host_resources

    @property
    def kube_clusters(self):
        """ This is a list of raw Kube clusters.
        """
        kube_cluster_list = []
        for kube_cluster in self.connection.kube_cluster.list():
            kube_cluster_list.append(kube_cluster)
        return kube_cluster_list

    @property
    def kube_cluster_resources(self):
        """ This is a list of the Kubernetes resource objects.
        I.e. interfaces for storing properties in runtime, etc.
        """
        kube_cluster_resources = []
        if not self._kube_cluster_resources:
            for kube_cluster in self.kube_clusters:
                kube_cluster_resources.append(
                    KubeClusterResource(
                        client_config=self.client_config,
                        resource_config={
                            'cluster_name': kube_cluster.cluster_name
                        },
                        logger=self.logger))
            self._kube_cluster_resources = kube_cluster_resources
        return self._kube_cluster_resources

    @property
    def service_parameters(self):
        """ This is a list of raw service parameters.
        """
        service_parameter_list = []
        for service_parameter in self.connection.service_parameter.list():
            service_parameter_list.append(service_parameter)
        return service_parameter_list

    @property
    def openstack_cluster_resource(self):
        """ This is a list of the Openstack resource objects.
        I.e. interfaces for storing properties in runtime, etc.
        """
        service_parameter_resources = []
        if not self._service_parameter_resources:
            for service_parameter in self.service_parameters:
                if service_parameter.service != 'openstack':
                    continue
                service_parameter_resources.append(
                    ServiceParameterResource(
                        client_config=self.client_config,
                        resource_config={
                            'uuid': service_parameter.uuid
                        },
                        logger=self.logger))
            self._service_parameter_resources = service_parameter_resources
        return self._service_parameter_resources


class HostResource(ConfigurationResource):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._host_resources = None

    def list(self):
        return self.connection.ihost.list()

    def get(self):
        return self.connection.ihost.get(self.resource_id)

    def to_dict(self):
        return {
            self.resource_id: {
                'hostname': self.resource.hostname,
                'personality': self.resource.personality,
                'capabilities': self.resource.capabilities,
                'subfunctions': self.resource.subfunctions
            }
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


class KubeClusterResource(ConfigurationResource):
    id_key = 'cluster_name'

    def list(self):
        return self.connection.kube_cluster.list()

    def get(self):
        return self.connection.kube_cluster.get(self.resource_id)

    def to_dict(self):
        return {
            self.resource.cluster_name: {
                'admin_user': self.resource.admin_user,
                'admin_token': self.resource.admin_token,
                'cluster_api_endpoint': self.resource.cluster_api_endpoint,
                'admin_client_cert': self.resource.admin_client_cert,
                'cluster_name': self.resource.cluster_name,
                'cluster_ca_cert': self.resource.cluster_ca_cert,
                'cluster_version': self.resource.cluster_version,
                'admin_client_key': self.resource.admin_client_key
            }
        }


class ServiceParameterResource(ConfigurationResource):
    id_key = 'uuid'

    def list(self):
        return self.connection.service_parameter.list()

    def get(self):
        return self.connection.service_parameter.get(self.resource_id)

    def value(self):
        return self.resource.value

    def to_dict(self):
        return {
            self.resource.value: {
                'service': self.resource.service,
                'section': self.resource.section,
                'name': self.resource.name,
                'value': self.resource.value,
            }
        }
