import re
import time
from datetime import datetime, timedelta

from cloudify.decorators import workflow
from cloudify.workflows import ctx as wtx
from cloudify.exceptions import NonRecoverableError

from starlingx_server.sdk.cgts_client import UpgradeClient
from starlingx_server.sdk.dcmanager import StarlingxDcManagerClient
from upgrade_deployment_manager import upgrade_deployment_manager

from ..decorators import with_starlingx_resource
from cloudify_starlingx_sdk.resources.configuration import SystemResource
from starlingx_server.sdk.keystone_auth import SYSINV_API_URL


@with_starlingx_resource(SystemResource)
def upgrade(resource, sw_version=None, license_file_path='', iso_path='', sig_path='', type_of_strategy="upgrade",
            subcloud_apply_type='serial', strategy_action='', max_parallel_subclouds=1, stop_on_failure=True,
            group_name='', force_flag=True, ctx=None):
    client_config = resource.client_config
    auth_url = client_config.get('os_auth_url')
    username = client_config.get('os_username')
    password = client_config.get('os_password')
    project_name = client_config.get('os_project_name')
    user_domain_name = client_config.get('os_user_domain_name', None)
    project_domain_name = client_config.get('os_project_domain_name', None)
    user_domain_id = client_config.get('os_user_domain_id', None)
    project_domain_id = client_config.get('os_project_domain_id', None)
    verify_value = True if client_config.get('insecure', None) else False

    host_runtime_properties = ctx.instance.runtime_properties.get('hosts', {})
    controllers_list = sorted([v["hostname"] for k, v in host_runtime_properties.items()
                               if v["subfunctions"] == "controller"])
    workers_list = sorted([v["hostname"] for k, v in host_runtime_properties.items() if v["subfunctions"] == "worker"])
    storage_list = sorted([v["hostname"] for k, v in host_runtime_properties.items() if v["subfunctions"] == "storage"])

    upgrade_client = UpgradeClient.get_upgrade_client(auth_url=auth_url, username=username, password=password,
                                                      endpoint_type=SYSINV_API_URL,
                                                      project_name=project_name,
                                                      user_domain_name=user_domain_name,
                                                      project_domain_name=project_domain_name,
                                                      user_domain_id=user_domain_id,
                                                      project_domain_id=project_domain_id,
                                                      verify=verify_value)

    dc_patch_client = StarlingxDcManagerClient.get_patch_client(auth_url=auth_url, username=username, password=password,
                                                                project_name=project_name,
                                                                user_domain_name=user_domain_name,
                                                                project_domain_name=project_domain_name,
                                                                user_domain_id=user_domain_id,
                                                                project_domain_id=project_domain_id,
                                                                verify=verify_value)
    # Upgrade steps
    load_id = _upgrade_controllers(ctx=ctx, upgrade_client=upgrade_client, controllers_list=controllers_list,
                                   license_file_path=license_file_path, iso_path=iso_path, sig_path=sig_path,
                                   force_flag=force_flag)
    _upgrade_storage_node(upgrade_client=upgrade_client, storage_node_list=storage_list, force_flag=force_flag)
    _upgrade_worker_nodes(ctx=ctx, upgrade_client=upgrade_client, workers_list=workers_list, force_flag=force_flag)
    _finish_upgrade(upgrade_client, controllers_list, load_id=load_id, force_flag=force_flag)
    # 22. Upgrade Deployment Manager
    upgrade_deployment_manager(sw_version=sw_version)
    # 23. Upgrade subclouds (same as patch, just different strategy type)
    # 23.0 Create upgrade strategy
    resp, _code = dc_patch_client.get_subcloud_update_strategy(type_of_strategy=type_of_strategy)
    if _code < 300:
        dc_patch_client.delete_update_strategy(type_of_strategy=type_of_strategy)
    dc_patch_client.create_subcloud_update_strategy(type_of_strategy=type_of_strategy,
                                                    cloud_name=group_name,
                                                    max_parallel_subclouds=max_parallel_subclouds,
                                                    stop_on_failure=stop_on_failure,
                                                    subcloud_apply_type=subcloud_apply_type)

    # 23.1 Apply upgrade strategy
    dc_patch_client.execute_action_on_strategy(type_of_strategy=type_of_strategy, action=strategy_action)
    # 23.2 get all subclouds
    list_of_subclouds = dc_patch_client.get_list_of_subclouds()
    # 23.3 Check each subcloud status
    for subcloud in list_of_subclouds:
        details, _code = dc_patch_client.get_subcloud_details(subcloud=subcloud)  #TODO
    # 23.4 Delete upgrade strategy
    dc_patch_client.delete_update_strategy(type_of_strategy=type_of_strategy)


def _upgrade_controllers(ctx, upgrade_client, controllers_list, license_file_path, iso_path, sig_path, force_flag=True):
    # Make sure we are connected to controller-0
    health_status = upgrade_client.get_system_upgrade_health()
    status = True if re.findall('Fail|NOK', health_status) else False
    if status:
        ctx.logger.error('Health problem...\n{}'.format(health_status))
        raise NonRecoverableError
    if len(controllers_list) > 1:
        controller0 = controllers_list[0]
        controller1 = controllers_list[1]
        active_controller = upgrade_client.get_active_controller()
        if controller0 != active_controller:
            ctx.logger.error('ACTIVE Controller is different than expected.\n'
                             ' Current active node: {}'.format(active_controller))
            raise NonRecoverableError

    # 1. Install license for new release
    resp = upgrade_client.apply_license(license_file_path=license_file_path)
    if 'Success: new license installed' not in resp.get('success', ''):
        ctx.logger.error('License not installed: {}'.format(resp))
        raise NonRecoverableError
    # 2. Upload ISO and SIG files to controller-0
    out = upgrade_client.upload_iso_and_sig_files(iso_path=iso_path, sig_path=sig_path, active='false')
    try:
        load_id = out.id
    except AttributeError:
        ctx.logger.error('Iso not loaded: {}'.format(str(out)))
        raise AttributeError

    if len(controllers_list) <= 1:
        controller = controllers_list[0]
        upgrade_client.do_upgrade_start(force=force_flag)
        # 4. Verify that upgrade has started
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='started')
        # 5. Lock controller-1
        upgrade_client.do_host_lock(hostname_or_id=controller, force=force_flag)
        _controller_is_locked(upgrade_client=upgrade_client, controller_name=controller)
        # 6. Upgrade controller-1
        upgrade_client.do_host_upgrade(host_id=controller, force=force_flag)
        # 7. Check upgrade status
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='data-migration')
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='data-migration-complete',
                                timeout=15 * 60)
        # 8. Unlock controller-1
        upgrade_client.do_host_unlock(hostname_or_id=controller, force=force_flag)
        _controller_is_unlocked(upgrade_client=upgrade_client, controller_name=controller)
    else:
        controller0 = controllers_list[0]
        controller1 = controllers_list[1]
        # 3. Run upgrade start
        try:
            status = upgrade_client.do_upgrade_start(force=force_flag).state
            state = status.state
            if 'starting' not in state:
                ctx.logger.error('WRONG STATUS: {}'.format(status))
                raise NonRecoverableError
        except AttributeError:
            ctx.logger.error('Upgrade start ERROR: {}'.format(status))
            raise NonRecoverableError
        # 4. Verify that upgrade has started
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='started')
        # 5. Lock controller-1
        upgrade_client.do_host_lock(hostname_or_id=controller1, force=force_flag)
        _controller_is_locked(upgrade_client=upgrade_client, controller_name=controller1)
        # 6. Upgrade controller-1
        upgrade_client.do_host_upgrade(host_id=controller1, force=force_flag)
        # 7. Check upgrade status
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='data-migration')
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='data-migration-complete', timeout=15*60) # TODO
        # 8. Unlock controller-1
        upgrade_client.do_host_unlock(hostname_or_id=controller1, force=force_flag)
        _controller_is_unlocked(upgrade_client=upgrade_client, controller_name=controller1)
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='upgrading-controllers', timeout=15 * 60)


        # 10. TBD: Wait for the DRBD sync 400.001 Services-related alarm is raised and then cleared
        # 11. Set controller-1 as active controller
        upgrade_client.do_host_swact(hostname_or_id=controller0, force=force_flag)
        # 12. Wait for all services on controller-1 are enabled-active, the swact is complete
        upgrade_client.wait_for_swact()
        active_controller = upgrade_client.get_active_controller()
        if controller1 != active_controller:
            ctx.logger.error('Active controller is different than expected')
            raise NonRecoverableError
        # 13. Lock controller-0
        upgrade_client.do_host_lock(hostname_or_id=controller0, force=force_flag)
        _controller_is_locked(upgrade_client=upgrade_client, controller_name=controller0)
        # 14. Upgrade controller-0
        upgrade_client.do_host_upgrade(host_id=controller0, force=force_flag)
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='data-migration')
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='data-migration-complete',
                                timeout=15 * 60)
        # 15. Unlock Controller-0
        upgrade_client.do_host_unlock(hostname_or_id=controller0, force=force_flag)
        _controller_is_unlocked(upgrade_client=upgrade_client, controller_name=controller0)
        return load_id


def _upgrade_storage_node(ctx, upgrade_client, storage_node_list=None, force_flag=True):
    # 16. Upgrde ceph sotrage (if in use) - repeat for each storage node
    # # 16.1 Get sorage nodes list
    # upgrade_client.do_host_list()
    for host in storage_node_list:
        # 16.2 Lock storage node
        # 16.3 Verify that storage node is locked
        upgrade_client.do_host_lock(hostname_or_id=host, force=force_flag)
        _controller_is_locked(upgrade_client=upgrade_client, controller_name=host)
        # 16.4 Upgrade system storage
        upgrade_client.do_host_upgrade(host_id=host, force=force_flag)
        # 16.5 Unlock storage node
        upgrade_client.do_host_unlock(hostname_or_id=host, force=force_flag)
        _controller_is_unlocked(upgrade_client=upgrade_client, controller_name=host)


def _upgrade_worker_nodes(ctx, upgrade_client, workers_list, force_flag=True):
    # 17. Upgrade worker nodes - repeat for each worker node
    # # 17.1 Get worker node list
    # upgrade_client.do_host_list()
    for host in workers_list:
        # 17.2 lock worker node
        upgrade_client.do_host_lock(hostname_or_id=host, force=force_flag)
        _controller_is_locked(upgrade_client=upgrade_client, controller_name=host)
        # 17.3 Upgrade worker node
        upgrade_client.do_host_upgrade(host_id=host, force=force_flag)
        # 17.4 Unlock worker node
        upgrade_client.do_host_unlock(hostname_or_id=host, force=force_flag)
        _controller_is_unlocked(upgrade_client=upgrade_client, controller_name=host)


def _finish_upgrade(upgrade_client, controllers_list, load_id, force_flag=True):
    if len(controllers_list) <= 1:
        upgrade_client.do_upgrade_activate()
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='activation-complete', timeout=15 * 60)
        upgrade_client.do_upgrade_complete()
        upgrade_client.delete_load(load_id)
    else:
        controller0 = controllers_list[0]
        controller1 = controllers_list[1]
        # 18 Set controller-0 as active
        upgrade_client.do_host_swact(hostname_or_id=controller1, force=force_flag)
        upgrade_client.wait_for_swact()
        active_controller = upgrade_client.get_active_controller()
        if controller0 != active_controller:
            raise NonRecoverableError
        # 19. Activate upgrade
        upgrade_client.do_upgrade_activate()
        # 20. Await for activation status complete
        _wait_for_upgrade_state(upgrade_client=upgrade_client, expected_state='activation-complete', timeout=15 * 60)
        # 21. Complete the upgrade
        upgrade_client.do_upgrade_complete()


def _controller_is_unlocked(upgrade_client, controller_name, timeout: int = 15):
    # 9. Wait for controller-1 to become unlocked-enabled
    timeout_start = datetime.now()
    while datetime.now() < timeout_start + timedelta(seconds=timeout):
        state = upgrade_client.do_host_show(hostname_or_id=controller_name).administrative
        if state == 'unlocked':
            return
        time.sleep(1)
    raise NonRecoverableError


def _controller_is_locked(upgrade_client, controller_name, timeout: int = 15):
    # 9. Wait for controller-1 to become unlocked-enabled
    timeout_start = datetime.now()
    while datetime.now() < timeout_start + timedelta(seconds=timeout):
        state = upgrade_client.do_host_show(hostname_or_id=controller_name).administrative
        if state == 'locked':
             return
        time.sleep(1)
    raise NonRecoverableError


def _wait_for_upgrade_state(upgrade_client, expected_state, timeout: int = 30):
    timeout_start = datetime.now()
    while datetime.now() < timeout_start + timedelta(seconds=timeout):
        state = upgrade_client.do_upgrade_show().state
        if state == expected_state:
            return
        time.sleep(1)
    raise NonRecoverableError
