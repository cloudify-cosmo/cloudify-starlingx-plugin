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
        :param global_request_id:
        :param region_name:
        :param endpoint_type:
        :param verify: check SSL certs
        """
        insecure = True if not verify else False
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

        system_url = all_endpoints[SYSINV_API_URL]
        system_url = 'http://localhost:6385'
        return cls(token=token, endpoint_type=endpoint_type, region_name=region_name,
                   global_request_id=global_request_id,
                   insecure=insecure, system_url=system_url)

    def __init__(self, token: str, endpoint_type: str, region_name: str, global_request_id: str, system_url: str,
                 insecure=False):
        self.client = get_client(api_version='1', os_auth_token=token, os_endpoint_type=endpoint_type,
                                 os_region_name=region_name, global_request_id=global_request_id, insecure=insecure,
                                 system_url=system_url)

    def apply_license(self, license_file_path: str) -> Any:
        """
        Applies license from file.

        :param license_file_path:

        :rtype: Any
        """

        # license_manager = LicenseManager(api=self.client)
        # license_manager.install_license(file=license_file_path)
        self.client.license.install_license(file=license_file_path)

    def upload_iso_and_sig_files(self, iso_path, sig_path, active='true', local='true'):
        """
        Upload iso and sig files.

        :param iso_path: Absolute path
        :param sig_path: Relative path
        :param active:
        :param local:
        """

        body = {
            'path_to_iso': iso_path,
            'path_to_sig': sig_path,
            'active': active,
            'local': local,
        }

        imported_load = self.client.load.import_load(**body)

        return imported_load

    def do_upgrade_start(self, force):
        """
        Starts a software upgrade.

        :type force:
        """

        upgrade = self.client.upgrade.create(force)
        uuid = getattr(upgrade, 'uuid', '')
        try:
            upgrade = self.client.upgrade.get(uuid)
        except exc.HTTPNotFound:
            raise exc.CommandError('Created upgrade UUID not found: %s' % uuid)
        _print_upgrade_show(upgrade)

    def do_upgrade_show(self):
        """
        Shows software upgrade details and attributes.
        """

        upgrades = self.client.upgrade.list()
        if upgrades:
            _print_upgrade_show(upgrades[0])
        else:
            print('No upgrade in progress')

    def do_host_lock(self, hostname_or_id, force=True):
        """
        Locks a host.

        :param force:
        :type hostname_or_id: object
        """

        attributes = []

        if force is True:
            # Forced lock operation
            attributes.append('action=force-lock')
        else:
            # Normal lock operation
            attributes.append('action=lock')

        patch = utils.args_array_to_patch("replace", attributes)
        ihost = ihost_utils._find_ihost(self.client, hostname_or_id)
        try:
            ihost = self.client.ihost.update(ihost.id, patch)
        except exc.HTTPNotFound:
            raise exc.CommandError('host not found: %s' % hostname_or_id)
        _print_ihost_show(ihost)

    def do_host_upgrade(self, host_id, force=True):
        """
        Performs software upgrade for a host.
        :param force:
        :param host_id:
        """

        ihost_utils._find_ihost(self.client, host_id)
        system_type, system_mode = utils._get_system_info(self.client)
        simplex = system_mode == constants.SYSTEM_MODE_SIMPLEX

        if simplex:
            warning_message = (
                '\n'
                'WARNING: THIS OPERATION WILL COMPLETELY ERASE ALL DATA FROM THE '
                'SYSTEM.\n'
                'Only proceed once the system data has been copied to another '
                'system.\n'
                'Are you absolutely sure you want to continue?  [yes/N]: ')
            confirm = input(warning_message)
            if confirm != 'yes':
                print("Operation cancelled.")
                return

        ihost = self.client.ihost.upgrade(host_id, force)
        _print_ihost_show(ihost)

    def do_host_unlock(self, hostname_or_id, force=True):
        """
        Unlocks a host.
        :param force:
        :param hostname_or_id:
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
            ihost = self.client.ihost.update(ihost.id, patch)
        except exc.HTTPNotFound:
            raise exc.CommandError('host not found: %s' % hostname_or_id)
        _print_ihost_show(ihost)

    def do_host_show(self, hostname_or_id, column='', format=''):
        """
        Shows host attributes.

        :param hostname_or_id:
        :param column:
        :param format:
        """

        ihost = ihost_utils._find_ihost(self.client, hostname_or_id)
        _print_ihost_show(ihost, column, format)
        return ihost

    def do_host_swact(self, hostname_or_id, force=True):
        """
        Switches activity away from this active host.

        :param hostname_or_id:
        :param force:
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
        except exc.HTTPNotFound:
            raise exc.CommandError('host not found: %s' % hostname_or_id)
        _print_ihost_show(ihost)

    def wait_for_swact(self):
        """
        Waits for all services on controller-1 are enabled-active, the swact is complete.
        """

        i = iServiceManager(api=self.client)

        return i.list()

    def do_host_list(self, column='', format=''):
        """
        Lists hosts.

        :param column:
        :param format:
        """

        ihosts = self.client.ihost.list()

        if column:
            fields = column
        else:
            fields = ['id', 'hostname', 'personality', 'administrative',
                      'operational', 'availability']

        utils.print_list(ihosts, fields, fields, sortby=0,
                         output_format=format)
        return ihosts

    def do_upgrade_activate(self):
        """
        Activate a software upgrade.
        """

        data = dict()
        data['state'] = constants.UPGRADE_ACTIVATION_REQUESTED

        patch = []
        for (k, v) in data.items():
            patch.append({'op': 'replace', 'path': '/' + k, 'value': v})
        try:
            upgrade = self.client.upgrade.update(patch)
        except exc.HTTPNotFound:
            raise exc.CommandError('Upgrade UUID not found')
        _print_upgrade_show(upgrade)

    def do_upgrade_complete(self):
        """
        Complete a software upgrade.
        """

        try:
            upgrade = self.client.upgrade.delete()
        except exc.HTTPNotFound:
            raise exc.CommandError('Upgrade not found')

        _print_upgrade_show(upgrade)
    
    def get_system_upgrade_health(self):
        """
            get system health: system health-query-upgrade
        """
        return self.client.health.get_upgrade()
    
    def get_load_list(self):
        """
        system load-list
        """
        return self.client.load.list()
    
    def delete_load(self, load_id):
        """
        system load-delete 1
        """
        return self.client.load.delete(load_id)

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


