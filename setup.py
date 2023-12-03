# Copyright (c) 2021 Cloudify Platform Ltd. All rights reserved
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
import re
import sys
import pathlib
from setuptools import setup, find_packages



def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(current_dir, 'cloudify_starlingx/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


install_requires = [
    'python-keystoneclient==3.21.0',
    'openstacksdk==0.15.0',
    'httplib2',
]

if sys.version_info.major == 3 and sys.version_info.minor == 6:
    packages=[
        'cloudify_starlingx',
        'cloudify_starlingx_sdk',
    ]
    install_requires += [
        'distributedcloud-client @ git+https://github.com/starlingx/' \
        'distcloud-client.git@r/stx.4.0#egg=distributedcloud-client' \
        '&subdirectory=distributedcloud-client',
        'cgtsclient @ git+https://github.com/starlingx/' \
        'config.git@r/stx.4.0#egg=cgtsclient' \
        '&subdirectory=sysinv/cgts-client/cgts-client',
        'cloudify-common>=6.4.2,<7.0.0',
    ]
else:
    packages = find_packages()
    install_requires += [
        'distributedcloud-client',
        'cgtsclient',
        'fusion-common',
    ]

setup(
    name="cloudify-starlingx-plugin",
    version=get_version(),
    author="Cloudify.Co",
    author_email="cosmo-admin@cloudify.co",
    packages=packages,
    license="LICENSE",
    description="Represent StarlingX Workloads in Cloudify.",
    install_requires=install_requires
)
