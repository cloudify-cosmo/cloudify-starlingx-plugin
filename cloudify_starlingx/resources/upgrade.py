from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx
from cloudify_terminal_sdk.terminal_connection import SmartConnection
from cloudify.exceptions import NonRecoverableError

from ...starlingx_server.sdk.cgtsclient import UpgradeClient
from ...starlingx_server.sdk.dcmanager import StarlingxDcManagerClient
from upgrade_deployment_manager import upgrade_deployment_manager

from ..decorators import with_starlingx_resource
from cloudify_starlingx_sdk.resources.configuration import SystemResource
from ...starlingx_server.sdk.keystone_auth import DC_MANAGER_API_URL

@with_starlingx_resource(SystemResource)
def upgrade(resource, sw_version=None, license_file_path='', iso_path='', sig_path='', ctx=None, **_):
    client_config = resource.client_config
    auth_url = client_config.get('auth_url')
    username = client_config.get('username')
    password = client_config.get('api_key')
    project_name = client_config.get('project_name')
    user_domain_id = client_config.get('user_domain_id')
    project_domain_id = client_config.get('project_domain_id')

    host_runtime_properties = ctx.instance.runtime_properties.get('hosts', {})
    controllers_list = sorted([v["hostname"] for k, v in host_runtime_properties.items() if v["subfunctions"] == "controller"])
    workers_list = sorted([v["hostname"] for k, v in host_runtime_properties.items() if v["subfunctions"] == "worker"])
    storage_list = sorted([v["hostname"] for k, v in host_runtime_properties.items() if v["subfunctions"] == "worker"])

    upgrade_client = UpgradeClient.get_upgrade_client(auth_url=auth_url, username=username , password=password, endpoint_type=DC_MANAGER_API_URL,
                                                      project_name=project_name, user_domain_id=user_domain_id,
                                                      project_domain_id=project_domain_id)

    # Upgrade steps
    _upgrade_controlers(upgrade_client, controllers_list, license_file_path, iso_path, sig_path)
    _upgrade_storage_node(upgrade_client, storage_list)
    _upgrade_worker_nodes(upgrade_client, workers_list)
    _finish_upgrade(upgrade_client, controllers_list)
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
    list_of_subclouds = dc_patch_client.get_list_of_subclouds()
    # 23.3 Check each subcloud status
    for subcloud in list_of_subclouds:
        details = dc_patch_client.get_subcloud_details(subcloud='')  #TODO
    # 23.4 Delete upgrade strategy
    dc_patch_client.delete_update_strategy(type_of_strategy='upgrade')


def _upgrade_controlers(upgrade_client, controllers_list, license_file_path, iso_path, sig_path):
    # Make sure we are connected to controller-0
    # 1. Install license for new release
    if len(controllers_list)<=1:
        pass  #TODO -> how update one controller
    else:
        controller0 = controllers_list[0]
        controller1 = controllers_list[1]
        active_controler = _get_active_controller()
        if controller0!=active_controler:
            raise NonRecoverableError
        upgrade_client.apply_license(license_file_path=license_file_path)
        # 2. Upload ISO and SIG files to controller-0
        upgrade_client.upload_iso_and_sig_files(iso_path=iso_path, sig_path=sig_path, active='true', local='true')
        # 3. Run upgrade start
        upgrade_client.do_upgrade_start(force=True)
        # 4. Verify that upgrade has started
        upgrade_client.do_upgrade_show()
        # 5. Lock controller-1
        upgrade_client.do_host_lock(hostname_or_id=controller1, force=True)
        # 6. Upgrade controller-1
        upgrade_client.do_host_upgrade(host_id=controller1, force=True)
        # 7. Check upgrade status
        upgrade_client.do_upgrade_show()
        # 8. Unlock controller-1
        upgrade_client.do_host_unlock(hostname_or_id=controller1 , force=True)
        _verify_unlock_controller(upgrade_client, controller1)
        # 10. TBD: Wait for the DRBD sync 400.001 Services-related alarm is raised and then cleared
        # 11. Set controller-1 as active controller
        upgrade_client.do_host_swact(hostname_or_id=controller0, force=True)
        # 12. Wait for all services on controller-1 are enabled-active, the swact is complete
        upgrade_client.wait_for_swact()
        active_controler = _get_active_controller()
        if controller1!=active_controler:
            raise NonRecoverableError
        # 13. Lock controller-0
        upgrade_client.do_host_lock(hostname_or_id=controller0, force=True)
        # 14. Upgrade controller-0
        upgrade_client.do_host_upgrade(host_id=controller0, force=True)
        # 15. Unlock Controller-0
        upgrade_client.do_host_unlock(hostname_or_id=controller0, force=True)
        _verify_unlock_controller(upgrade_client, controller0)


def _get_active_controller(upgrade_client):
    #TODO 
    pass


def _verify_unlock_controller(upgrade_client, controller_name):
    # 9. Wait for controller-1 to become unlocked-enabled
    output = upgrade_client.do_host_show(hostname_or_id=controller_name, column='', format='')


def _upgrade_storage_node(upgrade_client, storage_node_list=None):
    # 16. Upgrde ceph sotrage (if in use) - repeat for each storage node
    # # 16.1 Get sorage nodes list
    # upgrade_client.do_host_list(column='', format='')
    for host in storage_node_list:
        # 16.2 Lock storage node
        upgrade_client.do_host_lock(hostname_or_id=host, force=True)
        # 16.3 Verify that storage node is locked
        upgrade_client.do_host_show(hostname_or_id=host, column='', format='')
        # 16.4 Upgrade system storage
        upgrade_client.do_host_upgrade(host_id=host, force=True)
        # 16.5 Unlock storage node
        upgrade_client.do_host_unlock(hostname_or_id=host, force=True)


def _upgrade_worker_nodes(upgrade_client, workers_list):
    # 17. Upgrade worker nodes - repeat for each worker node
    # # 17.1 Get worker node list
    # upgrade_client.do_host_list(column='', format='')
    for host in workers_list:
        # 17.2 lock worker node
        upgrade_client.do_host_lock(hostname_or_id=host, force=True)
        # 17.3 Upgrade worker node
        upgrade_client.do_host_upgrade(host_id='', force=True)
        # 17.4 Unlock worker node
        upgrade_client.do_host_unlock(hostname_or_id='', force=True)



def _finish_upgrade(upgrade_client, controllers_list):
    if len(controllers_list)<=1:
        pass  #TODO -> how update one controller
    else:
        controller0 = controllers_list[0]
        controller1 = controllers_list[1]
    # 18 Set controller-0 as active
    upgrade_client.do_host_swact(hostname_or_id=controller1, force=True)
    upgrade_client.wait_for_swact()
    active_controler = _get_active_controller()
    if controller0!=active_controler:
            raise NonRecoverableError
    # 19. Activate upgrade
    upgrade_client.do_upgrade_activate()
    # 20. Await for activation status complete
    upgrade_client.do_upgrade_show()

    # 21. Complete the upgrade
    upgrade_client.do_upgrade_complete()

