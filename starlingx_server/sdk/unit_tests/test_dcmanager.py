import mock

from starlingx_server.sdk.dcmanager import StarlingxDcManagerClient, SubCloudObject


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value='v1')
def test_dcmanager_get_api_version(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_api_version()
    assert isinstance(ret, str)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_list_of_subclouds(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_api_version()
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_create_subcloud(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.create_subcloud(subcloud=SubCloudObject())
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_subcloud_details(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_subcloud_details(subcloud='cloud1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_subcloud_additional_details(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_subcloud_additional_details(subcloud='cloud1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_modify_subcloud(mock_client):
    # TODO: default variables set to ''
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.modify_subcloud(subcloud='cloud1', group_id=10)
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_reconfigure_subcloud(mock_client):
    # TODO: default variables set to ''
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.reconfigure_subcloud(subcloud='cloud1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_reinstall_subcloud(mock_client):
    # TODO: default variables set to ''
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.reinstall_subcloud(subcloud='cloud1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_restore_subcloud(mock_client):
    # TODO: default variables set to ''
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.restore_subcloud(subcloud='cloud1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_update_status_for_subcloud(mock_client):
    # TODO: default variables set to ''
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.update_status_for_subcloud(subcloud='cloud1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_delete_subcloud(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.delete_subcloud(subcloud='cloud1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value=['subgroup1'])
def test_dcmanager_list_of_subcloud_groups(mock_client):
    # TODO: returned value not defined
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.list_of_subcloud_groups()
    assert isinstance(ret, list)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_create_subcloud_groups(mock_client):
    # TODO: name is int type not str
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.create_subcloud_groups(name='name', description='description of group', max_parallel_subclouds=1,
                                        update_apply_type='update')
    assert isinstance(ret, dict)


def test_dcmanager_create_subcloud_groups_empty_name():
    # TODO: name is int type not str
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.create_subcloud_groups(name=None, description='description of group', max_parallel_subclouds=1,
                                        update_apply_type='update')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_subcloud_groups_information(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_subcloud_groups_information(subcloud_group='group1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_subclouds_part_of_subcloud_group(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_subclouds_part_of_subcloud_group(subcloud_group='group1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_modify_subcloud_groups(mock_client):
    # TODO: name is int type not str
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.modify_subcloud_groups(subcloud_group='group1', name='cloud1', description='super cloud', max_parallel_subclouds=1, update_apply_type='upgrade')
    assert isinstance(ret, dict)


def test_dcmanager_modify_subcloud_groups_empty_name():
    # TODO: name is int type not str
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.modify_subcloud_groups(name='', subcloud_group='sub1', description='', max_parallel_subclouds=2,
                                        update_apply_type='update')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_delete_subcloud_group(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.delete_subcloud_group(subcloud_group='group1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_alarms_for_subclouds(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_alarms_for_subclouds()
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_subcloud_update_strategy(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_subcloud_update_strategy(type_of_strategy='upgrade')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_create_subcloud_update_strategy(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.create_subcloud_update_strategy(cloud_name='cloud1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_delete_update_strategy(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.delete_update_strategy(type_of_strategy='upgrade')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_execute_action_on_strategy(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.execute_action_on_strategy(action='upgrade')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_all_strategy_steps_for_all_clouds(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_all_strategy_steps_for_all_clouds()
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_all_strategy_steps_for_cloud(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_all_strategy_steps_for_cloud(cloud_name='cloud1')
    assert isinstance(ret, dict)


def test_dcmanager_get_all_strategy_steps_for_cloud_empty_name():
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_all_strategy_steps_for_cloud(cloud_name='')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_subcloud_software_update_options(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_subcloud_software_update_options()
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_subcloud_software_update_options_for_subcloud(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_subcloud_software_update_options_for_subcloud(subcloud='sub1')
    assert isinstance(ret, dict)


def test_dcmanager_update_software_options_for_subcloud():
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.update_software_options_for_subcloud(subcloud='sub1', alarm_restriction_type='',
                                                      default_instance_action='',
                                                      max_parallel_workers=1,
                                                      storage_apply_type='',
                                                      worker_apply_type='')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_get_subcloud_software_update_options_for_subcloud_with_empty_parameters(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.get_subcloud_software_update_options_for_subcloud(subcloud='sub1')
    assert isinstance(ret, dict)


@mock.patch.object(StarlingxDcManagerClient, '_api_call', return_value={'error': ''})
def test_dcmanager_delete_update_options_for_subcloud(mock_client):
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.delete_update_options_for_subcloud(subcloud='sub1')
    assert isinstance(ret, dict)


def test_dcmanager_delete_update_options_for_subcloud_empty_name():
    client = StarlingxDcManagerClient(url='http://localhost:8080',
                                      headers={"Content-Type": "application/json; charset=utf-8",
                                               "X-Auth-Token": 'token'}, verify=False)
    ret = client.delete_update_options_for_subcloud(subcloud='')
    assert isinstance(ret, dict)