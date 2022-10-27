from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx
from cloudify_terminal_sdk.terminal_connection import SmartConnection
from cloudify.exceptions import NonRecoverableError

from ...starlingx_server.sdk.cgtsclient import UpgradeClient
from ...starlingx_server.sdk.dcmanager import StarlingxDcManagerClient
from upgrade_deployment_manager import upgrade_deployment_manager

from ..decorators import with_starlingx_resource
from cloudify_starlingx_sdk.resources.configuration import SystemResource


@with_starlingx_resource(SystemResource)
def upgrade(resource, sw_version=None, license_file_path='', ctx=None, **_):
    client_config = resource.client_config
    auth_url = client_config.get('auth_url')
    username = client_config.get('username')
    password = client_config.get('api_key')
    project_name = client_config.get('project_name')
    user_domain_id = client_config.get('user_domain_id')
    project_domain_id = client_config.get('project_domain_id')

    upgrade_client = UpgradeClient.get_upgrade_client(auth_url=auth_url, username=username , password=password,
                                                      project_name=project_name, user_domain_id=user_domain_id,
                                                      project_domain_id=project_domain_id)

    # Upgrade steps

    # Make sure we are connected to controller-0

    # 1. Install license for new release
    upgrade_client.apply_license(license_file_path=license_file_path)

    # 2. Upload ISO and SIG files to controller-0
    upgrade_client.upload_iso_and_sig_files(iso_path='', sig_path='', active='true', local='true')

    # 3. Run upgrade start
    upgrade_client.do_upgrade_start(force=True)

    # 4. Verify that upgrade has started
    upgrade_client.do_upgrade_show()

    # 5. Lock controller-1
    upgrade_client.do_host_lock(hostname_or_id='', force=True)

    # 6. Upgrade controller-1
    upgrade_client.do_host_upgrade(host_id='', force=True)

    # 7. Check upgrade status
    upgrade_client.do_upgrade_show()

    # 8. Unlock controller-1
    upgrade_client.do_host_unlock(hostname_or_id='', force=True)

    # 9. Wait for controller-1 to become unlocked-enabled
    upgrade_client.do_host_show(hostname_or_id='', column='', format='')

    # 10. TBD: Wait for the DRBD sync 400.001 Services-related alarm is raised and then cleared

    # 11. Set controller-1 as active controller
    upgrade_client.do_host_swact(hostname_or_id='', force=True)

    # 12. Wait for all services on controller-1 are enabled-active, the swact is complete
    upgrade_client.wait_for_swact()

    # 13. Lock controller-0
    upgrade_client.do_host_swact(hostname_or_id='', force=True)

    # 14. Upgrade controller-0
    upgrade_client.do_host_upgrade(host_id='', force=True)

    # 15. Unlock Controller-0
    upgrade_client.do_host_unlock(hostname_or_id='', force=True)

    # 16. Upgrde ceph sotrage (if in use) - repeat for each storage node

    # 16.1 Get sorage nodes list
    upgrade_client.do_host_list(column='', format='')

    # 16.2 Lock storage node
    upgrade_client.do_host_swact(hostname_or_id='', force=True)

    # 16.3 Verify that storage node is locked
    upgrade_client.do_host_show(hostname_or_id='', column='', format='')

    # 16.4 Upgrade system storage
    upgrade_client.do_host_upgrade(host_id='', force=True)

    # 16.5 Unlock storage node
    upgrade_client.do_host_unlock(hostname_or_id='', force=True)

    # 17. Upgrade worker nodes - repeat for each worker node

    # 17.1 Get worker node list
    upgrade_client.do_host_list(column='', format='')

    # 17.2 lock worker node
    upgrade_client.do_host_swact(hostname_or_id='', force=True)

    # 17.3 Upgrade worker node
    upgrade_client.do_host_upgrade(host_id='', force=True)

    # 17.4 Unlock worker node
    upgrade_client.do_host_unlock(hostname_or_id='', force=True)

    # 18 Set controller-1 as active
    upgrade_client.do_host_swact(hostname_or_id='', force=True)

    # 19. Activate upgrade
    upgrade_client.do_upgrade_activate()

    # 20. Await for activation status complete
    upgrade_client.do_upgrade_show()

    # 21. Complete the upgrade
    upgrade_client.do_upgrade_complete()

    # 22. Upgrade Deployment Manager
    upgrade_deployment_manager(sw_version=sw_version)

    # 23. Upgrade subclouds (same as patch, just different strategy type)

    dc_patch_client = StarlingxDcManagerClient.get_patch_client(api_url='', auth_url='', username='', password='',
                                                                project_name='', user_domain_id='',
                                                                project_domain_id='')

    # 23.0 Create upgrade strategy
    dc_patch_client.create_subcloud_update_strategy(type_of_strategy="upgrade", cloud_name="test_cloud",
                                                    max_parallel_subclouds=1, stop_on_failure=True,
                                                    subcloud_apply_type="serial")

    # 23.1 Apply upgrade strategy
    dc_patch_client.execute_action_on_strategy(type_of_strategy='upgrade')

    # 23.2 get all subclouds
    dc_patch_client.get_list_of_subclouds()

    # 23.3 Check each subcloud status

    dc_patch_client.get_subcloud_details(subcloud='')

    # 23.4 Delete upgrade strategy
    dc_patch_client.delete_update_strategy(type_of_strategy='upgrade')

