########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import pytest

from ecosystem_tests.dorkl import (
    basic_blueprint_test,
    cleanup_on_failure,
)

SECRETS_TO_CREATE = {
    'openstack_username': False,
    'openstack_password': False,
    'openstack_tenant_name': False,
    'openstack_project_name': False,
    'openstack_auth_url': False,
    'openstack_region': False,
    'base_image_id': False,
    'base_flavor_id': False,
    'openstack_user_domain_name': False,
    'openstack_project_domain_name': False,
}

blueprint_list = ['examples/blueprint.yaml']


@pytest.fixture(scope='function', params=blueprint_list)
def blueprint_examples(request):
    test_name = os.path.dirname(request.param).split('/')[-1:][0]
    try:
        basic_blueprint_test(
            request.param,
            test_name,
            inputs={'controller_uuid': '',
                    'controller_name': ''},
        )
    except Exception:
        cleanup_on_failure(test_name)
        raise


def test_blueprints(blueprint_examples):
    assert blueprint_examples is None
