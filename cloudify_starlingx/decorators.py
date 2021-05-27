# #######
# copyright (c) 2021 Cloudify Platform Ltd. All rights reserved
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

# Standard Imports
import os
import sys

# Third party imports
from cloudify import ctx as CloudifyContext
from cloudify.utils import exception_to_error_cause
from cloudify.exceptions import NonRecoverableError

from .utils import resolve_ctx, validate_auth_url, handle_cert_in_config


def with_starlingx_resource(class_decl):
    """
    :param class_decl: This is a class for the starlingx resource need to be
    invoked
    :return: a wrapper object encapsulating the invoked function
    """
    def wrapper_outer(func):
        def wrapper_inner(**kwargs):
            # Get the context for the current task operation
            ctx = kwargs.pop('ctx', CloudifyContext)

            # Resolve the actual context which need to run operation,
            # the context could be belongs to relationship context or actual
            # node context
            ctx_node = resolve_ctx(ctx)
            client_config = ctx_node.node.properties.get('client_config')
            cacert, cafile, cafilename = handle_cert_in_config(client_config)
            validate_auth_url(
                client_config['auth_url'],
                cacert,
                client_config.get('insecure'))
            resource_config = ctx_node.node.properties.get('resource_config')
            try:
                resource = class_decl(
                    client_config=client_config,
                    resource_config=resource_config,
                    logger=ctx.logger)
                func(resource, ctx)
            except Exception as errors:
                _, _, tb = sys.exc_info()
                if hasattr(errors, 'message'):
                    message = errors.message
                else:
                    message = ''
                raise NonRecoverableError(
                    'Failure while trying to run operation:'
                    '{0}: {1}'.format(ctx.operation.name, message),
                    causes=[exception_to_error_cause(errors, tb)])
            finally:
                if cafile and cafilename:
                    os.close(cafile)
                    os.remove(cafilename)
        return wrapper_inner
    return wrapper_outer
