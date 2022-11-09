import json

import requests

from starlingx_server.sdk.keystone_auth import get_token_from_keystone, get_endpoints, DC_MANAGER_API_URL


class SubCloudObject(object):
    bmc_password: str
    bootstrap_address: str
    bootstrap_values: str
    deploy_config: str
    description: str
    external_oam_floating_address: str
    external_oam_gateway_address: str
    external_oam_subnet: str
    group_id: int
    install_values: str
    location: str
    management_gateway_address: str
    management_end_ip: str
    management_start_address: str
    management_subnet: str
    migrate: bool
    name: str
    sysadmin_password: str
    systemcontroller_gateway_address: str
    system_mode: str


class StarlingxDcManagerClient(object):
    """
    StarlingX DcManager API client for specification taken from:
    https://docs.starlingx.io/api-ref/distcloud/api-ref-dcmanager-v1.html?expanded=#subcloud-groups
    """

    AVAILABLE_VERSION = 'v1.0'

    @classmethod
    def get_patch_client(cls, auth_url: str, username: str, password: str, project_name: str = 'admin',
                         user_domain_name: str = None, project_domain_name: str = None,
                         user_domain_id: str = None, project_domain_id: str = None, verify: bool = True):
        """
        Instantiate API client together with gathering token from Keystone.

        :param auth_url: URL for Keystone
        :param username: Username for Keystone
        :param password: Password for Keystone
        :param project_name: Project name for Keystone
        :param user_domain_name: User domain name for Keystone
        :param project_domain_name: Project domain name for Keystone
        :param user_domain_id: User domain ID for Keystone
        :param project_domain_id: Project domain ID for Keystone
        :param verify: check SSL certs
        """

        token = get_token_from_keystone(auth_url=auth_url, username=username, password=password,
                                        project_name=project_name,
                                        project_domain_name=project_domain_name, user_domain_name=user_domain_name,
                                        project_domain_id=project_domain_id, user_domain_id=user_domain_id,
                                        verify=verify)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "X-Auth-Token": token
        }

        all_endpoints = get_endpoints(auth_url=auth_url, headers=headers, verify=verify)
        return cls(url=all_endpoints[DC_MANAGER_API_URL], headers=headers, verify=verify)

    @classmethod
    def get_for_mock_server(cls, keystone_password: str):
        """
        This method will instantiate StarlingX client for Mock testing.
        """
        url = "http://localhost:8119"

        token = get_token_from_keystone(auth_url='http://localhost:5000/v3', username='admin',
                                        password=keystone_password, verify=False)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "X-Auth-Token": token
        }

        return cls(url=url, headers=headers, verify=False)

    def __init__(self, url: str, headers: dict, verify: bool):
        self.connection = None
        self.url = url
        self.headers = headers
        self.verify = verify

    def _api_call(self, api_call_type: requests, url='', headers=None, **kwargs):
        """
            General method to execute requests call
            :params - https://requests.readthedocs.io/en/latest/api/
            :rtype: dict or str
        """
        url = url or self.url
        headers = headers or self.headers
        verify = kwargs.pop('verify', None) or self.verify
        response = api_call_type(url=url, headers=headers, verify=verify, **kwargs)
        try:
            return response.json(), response.status_code
        except:
            return response.text, response.status_code

    def get_api_version(self) -> str:
        """
        This method returns information about supported version.

        :rtype: str
        """
        return self._api_call(api_call_type=requests.get)

    def get_list_of_subclouds(self) -> dict:
        """
        This method returns list of all subclouds.

        :rtype: list
        """
        endpoint = "{}/{}/subclouds".format(self.url, self.AVAILABLE_VERSION)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def create_subcloud(self, subcloud: SubCloudObject) -> dict:
        """
        This method creates a subcloud.

        :param subcloud: Subcloud to be created
        :rtype: dict
        """

        endpoint = "{}/{}/upload".format(self.url, self.AVAILABLE_VERSION)

        # We need to replace bootstrap_address property into bootstrap-address in json
        mapping = {
            "bootstrap_address": "bootstrap-address",
        }

        marshaled_object = json.dumps({mapping.get(k, k): v for k, v in subcloud.__dict__.items()})
        return self._api_call(api_call_type=requests.post, url=endpoint, data=marshaled_object, allow_redirects=False)

    def get_subcloud_details(self, subcloud: str) -> dict:
        """
        Shows information about a specific subcloud.

        :param subcloud: The subcloud reference, name or id
        :rtype: dict
        """

        endpoint = "{}/{}/subclouds/{}".format(self.url, self.AVAILABLE_VERSION, subcloud)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def get_subcloud_additional_details(self, subcloud: str) -> dict:
        """
        Shows additional information about a specific subcloud.

        :param subcloud: The subcloud reference, name or id
        :rtype: dict
        """

        endpoint = "{}/{}/subclouds/{}/detail".format(self.url, self.AVAILABLE_VERSION, subcloud)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def modify_subcloud(self, subcloud: str, group_id: int, description: str = '', location: str = '',
                        management_state: str = '') -> dict:
        """
        Modifies a specific subcloud.

        :param subcloud: The subcloud reference, name or id
        :param description: The description of a subcloud
        :param location: The location of a subcloud
        :param management_state: Management state of the subcloud
        :param group_id: The ID of the subcloud group associated with this object

        :rtype: dict
        """
        endpoint = "{}/{}/subclouds/{}".format(self.url, self.AVAILABLE_VERSION, subcloud)

        data = {}

        if description:
            data.update({'description': description})
        if location:
            data.update({'location': location})
        if management_state:
            data.update({'management-state': management_state})
        if group_id:
            data.update({'group_id': group_id})

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.patch, url=endpoint, data=marshaled_object, allow_redirects=False)

    def reconfigure_subcloud(self, subcloud: str, deploy_config: str = '', sysadmin_password: str = '') -> dict:
        """
        Modifies a specific subcloud.

        :param subcloud: The content of a file containing the resource definitions describing the desired subcloud configuration
        :param deploy_config: The description of a subcloud
        :param sysadmin_password: The sysadmin password of the subcloud. Must be base64 encoded

        :rtype: dict
        """
        endpoint = "{}/{}/subclouds/{}/reconfigure".format(self.url, self.AVAILABLE_VERSION, subcloud)

        if not deploy_config:
            return {
                'message': "deploy_config can not be empty",
                'error': "True",
            }
        if not sysadmin_password:
            return {
                'message': "sysadmin_password can not be empty",
                'error': "True",
            }

        data = {
            'deploy_config': deploy_config,
            'sysadmin_password': sysadmin_password,
        }

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.patch, url=endpoint, data=marshaled_object, allow_redirects=False)

    def reinstall_subcloud(self, subcloud: str, deploy_config: str = '', sysadmin_password: str = '',
                           bootstrap_values: str = '') -> dict:
        """
        Reinstall a specific subcloud.

        :param subcloud: The content of a file containing the resource definitions describing the desired subcloud
        configuration
        :param deploy_config: The description of a subcloud
        :param sysadmin_password: The sysadmin password of the subcloud. Must be base64 encoded
        :param bootstrap_values: The content of a file containing the bootstrap overrides such as subcloud name,
        management and OAM subnet.The sysadmin password of the subcloud. Must be base64 encoded

        :rtype: dict
        """

        endpoint = "{}/{}/subclouds/{}/reinstall".format(self.url, self.AVAILABLE_VERSION, subcloud)

        if not deploy_config:
            return {
                'message': "deploy_config can not be empty",
                'error': "True",
            }

        if not sysadmin_password:
            return {
                'message': "sysadmin_password can not be empty",
                'error': "True",
            }

        if not bootstrap_values:
            return {
                'message': "bootstrap_values can not be empty",
                'error': "True",
            }

        data = {
            'deploy_config': deploy_config,
            'sysadmin_password': sysadmin_password,
            'bootstrap_values': bootstrap_values,
        }

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.patch, url=endpoint, data=marshaled_object, allow_redirects=False)

    def restore_subcloud(self, subcloud: str, restore_values: str = '', sysadmin_password: str = '',
                         with_install: bool = False) -> dict:
        """
        Restores a specific subcloud from platform backup data.

        :param subcloud: The content of a file containing the resource definitions describing the desired subcloud
        configuration
        :param restore_values: The content of a file containing restore parameters (e.g. backup_filename)
        :param sysadmin_password: The sysadmin password of the subcloud. Must be base64 encoded
        :param with_install: The flag to indicate whether remote install is required or not (e.g. true)

        :rtype: dict
        """

        endpoint = "{}/{}/subclouds/{}/restore".format(self.url, self.AVAILABLE_VERSION, subcloud)

        if not restore_values:
            return {
                'message': "restore_values can not be empty",
                'error': "True",
            }

        if not sysadmin_password:
            return {
                'message': "sysadmin_password can not be empty",
                'error': "True",
            }

        data = {
            'restore_values': restore_values,
            'sysadmin_password': sysadmin_password,
        }

        if with_install:
            data.update({'with_install': with_install})

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.patch, url=endpoint, data=marshaled_object, allow_redirects=False)

    def update_status_for_subcloud(self, subcloud: str, updated_endpoint: str = '', status: str = '') -> dict:
        """
        Update the status of a specific subcloud.

        :param subcloud: The content of a file containing the resource definitions describing the desired subcloud
        configuration
        :param updated_endpoint: The endpoint that is being updated. Only supported value is: dc-cert
        :param status: The endpoint sync status. in-sync, out-of-sync, unknown

        :rtype: dict
        """

        endpoint = "{}/{}/subclouds/{}/update_status".format(self.url, self.AVAILABLE_VERSION, subcloud)

        if not updated_endpoint:
            return {
                'message': "endpoint can not be empty",
                'error': "True",
            }

        if not status:
            return {
                'message': "status can not be empty",
                'error': "True",
            }

        data = {
            'endpoint': updated_endpoint,
            'status': status,
        }

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.patch, url=endpoint, data=marshaled_object, allow_redirects=False)

    def delete_subcloud(self, subcloud: str) -> dict:
        """
        Delete a specific subcloud.

        :param subcloud: The content of a file containing the resource definitions describing the desired subcloud
        configuration

        :rtype: dict
        """

        endpoint = "{}/{}/subclouds/{}".format(self.url, self.AVAILABLE_VERSION, subcloud)

        return self._api_call(api_call_type=requests.delete, url=endpoint)

    # Subcloud Groups
    def list_of_subcloud_groups(self):
        """
        Lists all subcloud groups.

        :rtype: dict
        """

        endpoint = "{}/{}/subcloud-groups".format(self.url, self.AVAILABLE_VERSION)

        return self._api_call(api_call_type=requests.get, url=endpoint)

    def create_subcloud_groups(self, name: int, description: int, max_parallel_subclouds: int,
                               update_apply_type: str) -> dict:
        """
        Creates a subcloud group.

        :param name: The name of the subcloud group
        :param description: The description of the subcloud group
        :param max_parallel_subclouds: The maximum number of subclouds in the subcloud group to update in parallel
        :param update_apply_type: The method for applying an update to this subcloud group. serial or parallel

        :rtype: dict
        """

        endpoint = "{}/{}/subcloud-groups".format(self.url, self.AVAILABLE_VERSION)

        if not name:
            return {
                'message': "name can not be empty",
                'error': "True",
            }

        data = {
            'name': name,
        }

        if description:
            data.update({'description': description})

        if max_parallel_subclouds:
            data.update({'max_parallel_subclouds': max_parallel_subclouds})

        if update_apply_type:
            data.update({'update_apply_type': update_apply_type})

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.post, url=endpoint, data=marshaled_object)

    def get_subcloud_groups_information(self, subcloud_group: str) -> dict:
        """
        Shows information about a specific subcloud group.

        :param subcloud_group: The subcloud group reference, name or id
        :rtype: dict
        """

        endpoint = "{}/{}/subcloud-groups/{}".format(self.url, self.AVAILABLE_VERSION, subcloud_group)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def get_subclouds_part_of_subcloud_group(self, subcloud_group: str) -> dict:
        """
        Shows subclouds that are part of a subcloud group.

        :param subcloud_group: The subcloud group reference, name or id
        :rtype: dict
        """

        endpoint = "{}/{}/subcloud-groups/{}/subclouds".format(self.url, self.AVAILABLE_VERSION, subcloud_group)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def modify_subcloud_groups(self, subcloud_group: str, name: int, description: int, max_parallel_subclouds: int,
                               update_apply_type: str) -> dict:
        """
        Modify a subcloud group.

        :param subcloud_group: The subcloud group reference, name or id
        :param name: The name of the subcloud group
        :param description: The description of the subcloud group
        :param max_parallel_subclouds: The maximum number of subclouds in the subcloud group to update in parallel
        :param update_apply_type: The method for applying an update to this subcloud group. serial or parallel

        :rtype: dict
        """

        endpoint = "{}/{}/subcloud-groups/{}".format(self.url, self.AVAILABLE_VERSION, subcloud_group)

        if not name:
            return {
                'message': "name can not be empty",
                'error': "True",
            }

        data = {
            'name': name,
        }

        if description:
            data.update({'description': description})

        if max_parallel_subclouds:
            data.update({'max_parallel_subclouds': max_parallel_subclouds})

        if update_apply_type:
            data.update({'update_apply_type': update_apply_type})

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.patch, url=endpoint, data=marshaled_object)

    def delete_subcloud_group(self, subcloud_group: str) -> dict:
        """
        Delete a subcloud group.

        :param subcloud_group: The subcloud group reference, name or id

        :rtype: dict
        """

        endpoint = "{}/{}/subcloud-groups/{}".format(self.url, self.AVAILABLE_VERSION, subcloud_group)
        return self._api_call(api_call_type=requests.delete, url=endpoint)

    # Subcloud Alarms
    def get_alarms_for_subclouds(self) -> dict:
        """
        Subcloud alarms are aggregated on the System Controller.

        :rtype: dict
        """

        endpoint = "{}/{}/alarms".format(self.url, self.AVAILABLE_VERSION)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    # Subcloud Update Strategy
    def get_subcloud_update_strategy(self, type_of_strategy: str = None) -> dict:
        """
        The Subcloud update strategy is configurable.

        :param type_of_strategy: Filter to query a particular type of update strategy if it exists. One of: firmware,
        kube-rootca-update, kubernetes, patch, prestage, or upgrade

        :rtype: dict
        """
        if type_of_strategy:
            endpoint = "{}/{}/sw-update-strategy?type={}".format(self.url, self.AVAILABLE_VERSION, type_of_strategy)
        else:
            endpoint = "{}/{}/sw-update-strategy".format(self.url, self.AVAILABLE_VERSION)

        return self._api_call(api_call_type=requests.get, url=endpoint)

    def create_subcloud_update_strategy(self, cloud_name: str = None, type_of_strategy: str = None,
                                        max_parallel_subclouds: int = None, stop_on_failure: str = None,
                                        subcloud_apply_type: str = None) -> dict:
        """
        Creates the update strategy.

        :param type_of_strategy: Filter to query a particular type of update strategy if it exists. One of: firmware,
        kube-rootca-update, kubernetes, patch, prestage, or upgrade
        :param cloud_name: The name of a subcloud
        :param max_parallel_subclouds: The maximum number of subclouds to update in parallel
        :param stop_on_failure: Flag to indicate if the update should stop updating additional subclouds if a failure
        is encountered
        :param subcloud_apply_type: The apply type for the update. serial or parallel

        :rtype: dict
        """
        endpoint = "{}/{}/sw-update-strategy".format(self.url, self.AVAILABLE_VERSION)
        data = {}
        if cloud_name:
            data.update({'type': type_of_strategy})

        if type_of_strategy:
            data.update({'type': type_of_strategy})

        if max_parallel_subclouds:
            data.update({'max-parallel-subclouds': max_parallel_subclouds})

        if stop_on_failure:
            data.update({'stop-on-failure': stop_on_failure})

        if subcloud_apply_type:
            data.update({'subcloud-apply-type': subcloud_apply_type})

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.post, url=endpoint, data=marshaled_object)

    def delete_update_strategy(self, type_of_strategy: str = None) -> dict:

        """
        Deletes strategy.

        :param type_of_strategy: Filter to query a particular type of update strategy if it exists. One of: firmware,
        kube-rootca-update, kubernetes, patch, prestage, or upgrade

        :rtype: dict
        """

        if type_of_strategy:
            endpoint = "{}/{}/sw-update-strategy?type={}".format(self.url, self.AVAILABLE_VERSION, type_of_strategy)
        else:
            endpoint = "{}/{}/sw-update-strategy/".format(self.url, self.AVAILABLE_VERSION)
        return self._api_call(api_call_type=requests.delete, url=endpoint)

    # Subcloud Update Strategy Actions
    def execute_action_on_strategy(self, action: str, type_of_strategy: str = None) -> dict:
        """
        Executes an action on a patch strategy.

        :param type_of_strategy: Filter to query a particular type of update strategy if it exists. One of: firmware,
        kube-rootca-update, kubernetes, patch, prestage, or upgrade
        :param action: Perform an action on the update strategy. Valid values are: apply, or abort

        :rtype: dict
        """

        if not action:
            return {
                'message': "action can not be empty",
                'error': "True",
            }

        endpoint = "{}/{}/sw-update-strategy/actions".format(self.url, self.AVAILABLE_VERSION)
        data = {
            'action': action,
        }
        if type_of_strategy:
            data.update({'type': type_of_strategy})

        marshaled_object = json.dumps(data)
        return self._api_call(api_call_type=requests.post, url=endpoint, data=marshaled_object)

    # Subcloud Software Update Strategy Steps
    def get_all_strategy_steps_for_all_clouds(self) -> dict:
        """
        Subcloud patch strategy steps can be retrieved.

        :rtype: dict
        """
        endpoint = "{}/{}/sw-update-strategy/steps".format(self.url, self.AVAILABLE_VERSION)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def get_all_strategy_steps_for_cloud(self, cloud_name: str) -> dict:
        """
        Subcloud patch strategy steps for given cloud name.

        :param cloud_name: Cloud

        :rtype: dict
        """

        if not cloud_name:
            return {
                'message': "cloud_name can not be empty",
                'error': "True",
            }

        endpoint = "{}/{}/sw-update-strategy/steps/{}".format(self.url, self.AVAILABLE_VERSION, cloud_name)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    # Subcloud Software Update Options
    def get_subcloud_software_update_options(self) -> dict:
        """
        Lists all sw-update options.

        :rtype: dict
        """

        endpoint = "{}/{}/sw-update-options".format(self.url, self.AVAILABLE_VERSION)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def get_subcloud_software_update_options_for_subcloud(self, subcloud: str) -> dict:
        """
        Shows sw-update options (defaults or per subcloud.

        :param subcloud: The name of the subcloud to which the options apply. Use RegionOne for querying the default.

        :rtype: dict
        """

        if not subcloud:
            return {
                'message': "subcloud can not be empty",
                'error': "True",
            }

        endpoint = "{}/{}/sw-update-options/{}".format(self.url, self.AVAILABLE_VERSION, subcloud)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def update_software_options_for_subcloud(self, subcloud: str, alarm_restriction_type: str,
                                             default_instance_action: str, max_parallel_workers: int,
                                             storage_apply_type: str,
                                             worker_apply_type: str) -> dict:
        """
        Updates sw-update options, defaults or per subcloud.

        :param subcloud: The name of the subcloud to which the options apply. Use RegionOne for querying the default.
        :param alarm_restriction_type: Whether to allow update if subcloud alarms are present or not. Valid values are
        strict or relaxed
        :param default_instance_action: How instances should be handled. Valid values are stop-start or migrate
        :param max_parallel_workers: The maximum number of workers within a subcloud to update in parallel
        :param storage_apply_type: The apply type for the update on storage nodes in a subcloud.
        Valid values are: serial or parallel
        :param: worker_apply_type: The apply type for the update on worker nodes in a subcloud.
        Valid values are: serial or parallel.

        :rtype: dict
        """

        if not subcloud:
            return {
                'message': "subcloud can not be empty",
                'error': "True",
            }

        if not alarm_restriction_type:
            return {
                'message': "alarm_restriction_type can not be empty",
                'error': "True",
            }

        if not default_instance_action:
            return {
                'message': "default_instance_action can not be empty",
                'error': "True",
            }

        if not max_parallel_workers:
            return {
                'message': "max_parallel_workers can not be empty",
                'error': "True",
            }

        if not storage_apply_type:
            return {
                'message': "storage_apply_type can not be empty",
                'error': "True",
            }

        if not worker_apply_type:
            return {
                'message': "worker_apply_type can not be empty",
                'error': "True",
            }

        data = {
            'alarm-restriction-type': alarm_restriction_type,
            'default-instance-action': default_instance_action,
            'max-parallel-workers': max_parallel_workers,
            'storage-apply-type': storage_apply_type,
            'worker-apply-type': worker_apply_type,
        }

        marshaled_object = json.dumps(data)
        endpoint = "{}/{}/sw-update-options/{}".format(self.url, self.AVAILABLE_VERSION, subcloud)
        return self._api_call(api_call_type=requests.post, url=endpoint, data=marshaled_object)

    def delete_update_options_for_subcloud(self, subcloud: str) -> dict:
        """
        Delete per subcloud sw-update options.

        :param subcloud: The name of the subcloud to which the options apply. Use RegionOne for querying the default.

        :rtype: dict
        """

        if not subcloud:
            return {
                'message': "subcloud can not be empty",
                'error': "True",
            }

        endpoint = "{}/{}/sw-update-options/{}".format(self.url, self.AVAILABLE_VERSION, subcloud)
        return self._api_call(api_call_type=requests.delete, url=endpoint)

    # Subcloud Deploy
    def get_subcloud_deploy_files(self) -> dict:
        """
        Show Subcloud Deploy Files.

        :rtype: dict
        """

        endpoint = "{}/{}/subcloud-deploy".format(self.url, self.AVAILABLE_VERSION)
        return self._api_call(api_call_type=requests.get, url=endpoint)

    def upload_subcloud_deploy_files(self, deploy_chart: str, deploy_playbook: str, deploy_overrides: str,
                                     prestage_images: str, subcloud_deploy: dict) -> dict:
        """
        Upload Subcloud Deploy Files.

        :param deploy_chart: The file name of the deployment manager helm charts
        :param deploy_playbook: The file name of the deployment manager playbook
        :param deploy_overrides: The file name of the deployment manager overrides
        :param prestage_images: The file name of the deployment manager prestage images
        :param subcloud_deploy: The dictionary of subcloud deploy files

        :rtype: dict
        """

        pass
