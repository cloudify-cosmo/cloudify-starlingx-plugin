from email import utils
from typing import Any

from cgtsclient.common import constants
from cgtsclient.v1 import ihost as ihost_utils
from cgtsclient import exc
from cgtsclient.client import get_client
from cgtsclient.v1.iHost_shell import _print_ihost_show
from cgtsclient.v1.license import LicenseManager
from cgtsclient.v1.upgrade_shell import _print_upgrade_show


class UpgradeClient(object):
    def __init__(self, token: str):
        self.client = get_client(api_version=1, os_auth_token=token)

    def apply_license(self, license_file_path: str) -> Any:
        """
        Applies license from file.

        :param license_file_path:

        :rtype: Any
        """

        license_manager = LicenseManager(api=self.client)
        license_manager.install_license(file=license_file_path)

    def upload_iso_and_sig_files(self, cc, isopath, sigpath, active='true', local='true'):
        """
        Upload iso and sig files.

        :param cc:
        :param isopath: Absolute path
        :param sigpath: Relative path
        :param active:
        :param local:
        """

        body = {
            'path_to_iso': isopath,
            'path_to_sig': sigpath,
            'active': active,
            'local': local
        }

        imported_load = cc.load.import_load(**body)

        return imported_load

    def do_upgrade_start(self, cc, args):
        """Start a software upgrade. """

        upgrade = cc.upgrade.create(args.force)
        uuid = getattr(upgrade, 'uuid', '')
        try:
            upgrade = cc.upgrade.get(uuid)
        except exc.HTTPNotFound:
            raise exc.CommandError('Created upgrade UUID not found: %s' % uuid)
        _print_upgrade_show(upgrade)

    def do_upgrade_show(self, cc, args):
        """Show software upgrade details and attributes."""

        upgrades = cc.upgrade.list()
        if upgrades:
            _print_upgrade_show(upgrades[0])
        else:
            print('No upgrade in progress')

    def do_host_lock(self, cc, args):
        """Lock a host."""
        attributes = []

        if args.force is True:
            # Forced lock operation
            attributes.append('action=force-lock')
        else:
            # Normal lock operation
            attributes.append('action=lock')

        patch = utils.args_array_to_patch("replace", attributes)
        ihost = ihost_utils._find_ihost(cc, args.hostnameorid)
        try:
            ihost = cc.ihost.update(ihost.id, patch)
        except exc.HTTPNotFound:
            raise exc.CommandError('host not found: %s' % args.hostnameorid)
        _print_ihost_show(ihost)

    def do_host_upgrade(self, cc, args):
        """Perform software upgrade for a host."""
        ihost_utils._find_ihost(cc, args.hostid)
        system_type, system_mode = utils._get_system_info(cc)
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

        ihost = cc.ihost.upgrade(args.hostid, args.force)
        _print_ihost_show(ihost)