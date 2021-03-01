from cgtsclient.exc import HTTPNotFound
from dcmanagerclient.openstack.common.apiclient.exceptions import \
    EndpointNotFound

FATAL = (HTTPNotFound, EndpointNotFound)
