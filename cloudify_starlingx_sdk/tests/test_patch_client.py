import pytest

from cloudify_starlingx_sdk.common import StarlingxPatchClient


# Tests relies on https://github.com/marcin-cloudify/Cloudify-PS-StarlingxMock


# @pytest.mark.skip(reason="Make sure that mock server is running")
def test_get_api_version():
    client = StarlingxPatchClient.get_for_mock_server()
    api_version = client.get_api_version()
    assert api_version == "StarlingX Patching API, Available versions: /v1"
    assert isinstance(api_version, str)


# @pytest.mark.skip(reason="Make sure that mock server is running")
def test_get_list_of_patches():
    client = StarlingxPatchClient.get_for_mock_server()
    patches_list = client.get_list_of_patches()
    assert patches_list['pd']['TS_15.12_PATCH_0001']['status'] == 'REL'
    assert isinstance(patches_list, dict)


# @pytest.mark.skip(reason="Make sure that mock server is running")
def test_get_patch_details():
    patch_id = "TS_15.12_PATCH_0005"
    client = StarlingxPatchClient.get_for_mock_server()
    patch_details = client.get_patch_details(patch_id=patch_id)
    assert patch_details['contents'][patch_id][0] == "python-horizon-2013.2.3-r118.x86_64.rpm"
    assert patch_details['error'] == ""
    assert isinstance(patch_details, dict)


# @pytest.mark.skip(reason="To enable this test, make sure that mock server is running")
def test_upload_patch():
    patch = {
        "contents": {
            "TS_15.12_PATCH_0002": [
                "python-horizon-2013.2.3-r118.x86_64.rpm",
                "sysinv-1.0-r81.x86_64.rpm"
            ]
        },
        "error": "",
        "metadata": {
            "TS_15.12_PATCH_0002": {
                "description": "Fixes the following Issues:\n   compute-4 and storage-0 multiple resets after DOR",
                "install_instructions": "",
                "patchstate": "Partial-Remove",
                "repostate": "Available",
                "requires": ["Nothing"],
                "status": "DEV",
                "summary": "TS_15.12 Patch 0002",
                "sw_version": "15.12",
                "warnings": ""
            }
        }
    }
    client = StarlingxPatchClient.get_for_mock_server()
    out = client.upload_patch(patch=patch)
    assert out['info'] == 'TS_15.12_PATCH_0002 is now available\n'
    assert isinstance(out, dict)


# @pytest.mark.skip(reason="Make sure that mock server is running")
def test_apply_patch():
    patch_id = "TS_15.12_PATCH_0005"
    client = StarlingxPatchClient.get_for_mock_server()
    out = client.apply_patch(patch_id=patch_id)
    assert out['info'] == '{} has been applied\n'.format(patch_id)
    assert isinstance(out, dict)


# @pytest.mark.skip(reason="Make sure that mock server is running")
def test_remove_patch():
    patch_id = "TS_15.12_PATCH_0005"
    client = StarlingxPatchClient.get_for_mock_server()
    out = client.remove_patch(patch_id=patch_id)
    assert out['info'] == '{} has been removed from the repo\n'.format(patch_id)
    assert isinstance(out, dict)


# @pytest.mark.skip(reason="Make sure that mock server is running")
def test_delete_patch():
    patch_id = "TS_15.12_PATCH_0005"
    client = StarlingxPatchClient.get_for_mock_server()
    out = client.delete_patch(patch_id=patch_id)
    assert out['info'] == '{} has been deleted\n'.format(patch_id)
    assert isinstance(out, dict)


# @pytest.mark.skip(reason="Make sure that mock server is running")
def test_query_hosts():
    client = StarlingxPatchClient.get_for_mock_server()
    out = client.query_hosts()
    assert out[0]['hostname'] == 'Super-Host'
    assert isinstance(out, list)


# @pytest.mark.skip(reason="Make sure that mock server is running")
def test_host_install():
    hostname = "super_host"
    client = StarlingxPatchClient.get_for_mock_server()
    out = client.host_install(hostname=hostname)
    assert out['info'] == 'Patch installation request sent to {}.\n'.format(hostname)
    assert isinstance(out, dict)
