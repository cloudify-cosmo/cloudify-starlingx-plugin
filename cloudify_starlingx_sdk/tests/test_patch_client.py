import pytest

from cloudify_starlingx_sdk.common import StarlingxPatchClient

# Those tests should be enable once https://github.com/marcin-cloudify/Cloudify-PS-StarlingxMock is up and running


@pytest.mark.skip(reason="To enable this test, make sure that mock server is running")
def test_get_api_version():
    client = StarlingxPatchClient.get_for_mock_server()
    api_version = client.get_api_version()
    assert api_version == "StarlingX Patching API, Available versions: /v1"
    assert isinstance(api_version, str)


@pytest.mark.skip(reason="To enable this test, make sure that mock server is running")
def test_get_list_of_patches():
    client = StarlingxPatchClient.get_for_mock_server()
    patches_list = client.get_list_of_patches()
    assert patches_list['pd']['TS_15.12_PATCH_0001']['status'] == 'REL'
    assert isinstance(patches_list, dict)


@pytest.mark.skip(reason="To enable this test, make sure that mock server is running")
def test_get_patch_details():
    patch_id = "TS_15.12_PATCH_0005"
    client = StarlingxPatchClient.get_for_mock_server()
    patch_details = client.get_patch_details(patch_id=patch_id)
    assert patch_details['contents'][patch_id][0] == "python-horizon-2013.2.3-r118.x86_64.rpm"
    assert patch_details['error'] == ""
    assert isinstance(patch_details, dict)
