from email import utils
from typing import Any

from cgtsclient import exc
from cgtsclient.client import get_client
from cgtsclient.common import constants, utils
from cgtsclient.v1 import ihost as ihost_utils
from cgtsclient.v1.iHost_shell import _print_ihost_show
from cgtsclient.v1.iservice import iServiceManager
from cgtsclient.v1.license import LicenseManager
from cgtsclient.v1.upgrade_shell import _print_upgrade_show
from cgtsclient.v1.ihost import ihost as hostObj
from starlingx_server.sdk.keystone_auth import get_token_from_keystone, get_endpoints, SYSINV_API_URL


class UpgradeClient(object):
    @classmethod
    def get_upgrade_client(cls, auth_url: str, username: str, password: str, endpoint_type: str = '',
                           region_name: str = 'local', global_request_id: str = '', project_name: str = 'admin',
                           user_domain_name: str = None, project_domain_name: str = None,
                           user_domain_id: str = None, project_domain_id: str = None, verify: bool = True):
        """
        Instantiate API client together with gathering token from Keystone.

        :param auth_url: URL for Keystone
        :param username: Username for Keystone
        :param password: Password for Keystone
        :param project_name: Project name for Keystone
        :param user_domain_name: User domain  name for Keystone
        :param project_domain_name: Project domain name for Keystone
        :param user_domain_id: User domain ID for Keystone
        :param project_domain_id: Project domain ID for Keystone
        :param project_name:
        :param user_domain_id:
        :param global_request_id:
        :param region_name:
        :param endpoint_type:
        :param verify:
        """

        token = get_token_from_keystone(auth_url=auth_url, username=username, password=password,
                                        project_name=project_name,
                                        user_domain_id=user_domain_id, project_domain_id=project_domain_id,
                                        project_domain_name=project_domain_name, user_domain_name=user_domain_name,
                                        verify=verify)

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "X-Auth-Token": token
        }
        insecure = True if not verify else False
        all_endpoints = get_endpoints(auth_url=auth_url, headers=headers, verify=verify)

        system_url = all_endpoints[SYSINV_API_URL]
        system_url = 'http://localhost:6385'
        return cls(token=token, endpoint_type=endpoint_type, region_name=region_name,
                   global_request_id=global_request_id,
                   insecure=insecure, system_url=system_url)

    @classmethod
    def get_mock_client(cls, keystone_password: str):
        """
        Instantiate API client together with gathering token from Keystone.

        :param keystone_password: Password for Keystone admin
        """
        url = "http://localhost:6385"

        token = get_token_from_keystone(auth_url='http://localhost:5000/v3', username='admin',
                                        password=keystone_password)

        return cls(token=token, endpoint_type='', region_name='RegionOne',
                   global_request_id='',
                   insecure=True, system_url=url)

    def __init__(self, token: str, endpoint_type: str, region_name: str, global_request_id: str, system_url: str,
                 insecure=False):
        self.client = get_client(api_version='1', os_auth_token=token, os_endpoint_type=endpoint_type,
                                 os_region_name=region_name, global_request_id=global_request_id, insecure=insecure,
                                 system_url=system_url)

    def apply_license(self, license_file_path: str) -> str:
        """
        Applies license from file.

        :param license_file_path: Absolute path to the license file
        :rtype: str
        """
        try:
            with open(license_file_path, 'rb') as f:
                file_content = f.read()
            return self.client.license.install_license(file=file_content)
        except exc.HTTPException as e:
            return 'Not able to apply license: {}, code: {}, details: {}'.format(license_file_path, e.code, e.details)
        except Exception as e:
            return 'Unhandled exception: details: {}'.format(e)

    def upload_iso_and_sig_files(self, iso_path, sig_path, active='true', local='true') -> str:
        """
        Upload iso and sig files.

        :param iso_path: Absolute path
        :param sig_path: Relative path
        :param active:
        :param local:
        :rtype: str
        """

        body = {
            'path_to_iso': iso_path,
            'path_to_sig': sig_path,
            'active': active,
            'local': local,
        }
        try:
            out = self.client.load.import_load(**body)
            return 'Uploaded iso and sig files, details: {}'.format(out)
        except exc.HTTPException as e:
            return 'Not able to upload iso and sig files: {}, code: {}, details: {}'.format(iso_path, e.code, e.details)
        except Exception as e:
            return 'Unhandled exception: details: {}'.format(e)

    def do_upgrade_start(self, force) -> str:
        """
        Starts a software upgrade.

        :type force:
        :rtype: str
        """
        try:
            upgrade = self.client.upgrade.create(force)
            uuid = getattr(upgrade, 'uuid', '')
            upgrade = self.client.upgrade.get(uuid)
            return 'Started upgrade process, details: {}'.format(upgrade)
        except exc.HTTPException as e:
            return 'Not able to start upgrades, code: {}, details: {}'.format(e.code, e.details)

    def do_upgrade_show(self) -> list:
        """
        Shows software upgrade details and attributes.
        Returns empty list in case no servers in upgrade process.

        :rtype: list
        """

        return self.client.upgrade.list()

    def do_host_lock(self, hostname_or_id, force=True) -> str:
        """
        Locks a given host.

        :param force: Force flag to lock host
        :param hostname_or_id: Host or id for the given host
        :rtype: str
        """
        attributes = []

        if force is True:
            # Forced lock operation
            attributes.append('action=force-lock')
        else:
            # Normal lock operation
            attributes.append('action=lock')

        try:
            patch = utils.args_array_to_patch("replace", attributes)
            host = ihost_utils._find_ihost(self.client, hostname_or_id)
            out = self.client.ihost.update(host.id, patch)
            return 'Successfully locked host: {}, details: {}'.format(hostname_or_id, out)
        except exc.HTTPException as e:
            return 'Not able to lock host: {}, code: {}, details: {}'.format(hostname_or_id, e.code, e.details)

    def do_host_upgrade(self, host_id, force=True) -> str:
        """
        Performs software upgrade for a host.

        :param force: Force flag to upgrade host
        :param host_id: Host ID for the given host
        :rtype: str
        """
        try:
            out = self.client.ihost.upgrade(host_id, force)
            return 'Successfully upgraded host: {}, details: {}'.format(host_id, out)
        except exc.HTTPException as e:
            return 'Not able to upgrade host: {}, code: {}, details: {}'.format(host_id, e.code, e.details)

    def do_host_unlock(self, hostname_or_id, force=True) -> str:
        """
        Unlocks a host.

        :param force: Force to unlock
        :param hostname_or_id: Host or id for the given host
        :rtype: str
        """
        attributes = []

        if force is True:
            # Forced unlock operation
            attributes.append('action=force-unlock')
        else:
            # Normal unlock operation
            attributes.append('action=unlock')

        patch = utils.args_array_to_patch("replace", attributes)
        ihost = ihost_utils._find_ihost(self.client, hostname_or_id)
        try:
            out = self.client.ihost.update(ihost.id, patch)
            return 'Successfully unlocked host: {}, details: {}'.format(hostname_or_id, out)
        except exc.HTTPException as e:
            return 'Not able to unlock host: {}, code: {}, details: {}'.format(hostname_or_id, e.code, e.details)

    def do_host_show(self, hostname_or_id) -> str:
        """
        Shows host attributes.

        :param hostname_or_id: Host or id for the given host
        :rtype: str
        """

        try:
            out = ihost_utils._find_ihost(self.client, hostname_or_id)
            return out
        except exc.HTTPException as e:
            return 'Unable to show host: {}, code: {}, details: {}'.format(hostname_or_id, e.code, e.details)

    def do_host_swact(self, hostname_or_id, force=True) -> str:
        """
        Switches activity away from this active host.

        :param force: Force to unlock
        :param hostname_or_id: Host or id for the given host
        :rtype: str
        """
        attributes = []

        if force is True:
            # Forced swact operation
            attributes.append('action=force-swact')
        else:
            # Normal swact operation
            attributes.append('action=swact')

        patch = utils.args_array_to_patch("replace", attributes)
        ihost = ihost_utils._find_ihost(self.client, hostname_or_id)
        try:
            ihost = self.client.ihost.update(ihost.id, patch)
            return 'Activity was switched away from host: {}, details: {}'.format(hostname_or_id, ihost)
        except exc.HTTPNotFound as e:
            return 'host not found: {}, details: {}'.format(hostname_or_id, e.details)

    def wait_for_swact(self) -> list:
        """
        Waits for all services on controller-1 are enabled-active, the swact is complete.

        :rtype: list
        """

        i = iServiceManager(api=self.client)

        return i.list()

    def do_host_list(self) -> list:
        """
        Lists hosts.

        :rtype: list
        """

        hosts = self.client.ihost.list()
        return hosts

    def do_upgrade_activate(self) -> str:
        """
        Activate a software upgrade.

        :rtype: str
        """

        data = dict()
        data['state'] = constants.UPGRADE_ACTIVATION_REQUESTED

        patch = []
        for (k, v) in data.items():
            patch.append({'op': 'replace', 'path': '/' + k, 'value': v})
        try:
            out = self.client.upgrade.update(patch)
            return 'Software upgrade was activated successfully: {}'.format(out)
        except exc.HTTPException as e:
            return 'Software upgrade was not activated successfully: {}, details: {}'.format(e.code, e.details)

    def do_upgrade_complete(self):
        """
        Complete a software upgrade.
        """
        try:
            out = self.client.upgrade.delete()
            return 'Software upgrade was completed successfully: {}'.format(out)
        except exc.HTTPException as e:
            return 'Software upgrade was not activated successfully: {}, details: {}'.format(e.code, e.details)

    def get_system_upgrade_health(self) -> str:
        """
        Get system health: system health-query-upgrade.

        :rtype: str
        """
        try:
            out = self.client.health.get_upgrade()
            return 'Software health: {}'.format(out)
        except exc.HTTPException as e:
            return 'Unable to get system health: {}, details: {}'.format(e.code, e.details)

    def get_load_list(self) -> list:
        """
        system load-list

        :rtype: list
        """
        return self.client.load.list()

    def delete_load(self, load_id) -> str:
        """
        Delete load for given load ID.

        :rtype: str
        """
        try:
            out = self.client.load.delete(load_id)
            return 'Load ID: {} is deleted, details: {}'.format(load_id, out)
        except exc.HTTPException as e:
            return 'Unable to proceed request, http code: {}, details: {}'.format(e.code, e.details)

    def get_active_controller(self):
        host_name = ''
        for controller in self.do_host_list():
            if not isinstance(controller, hostObj):
                continue
            host_name = controller.hostname
            host_status = controller.capabilities['Personality']
            if host_status == 'Controller-Active':
                break
        return host_name
