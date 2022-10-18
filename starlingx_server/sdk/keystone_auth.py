from keystoneauth1.identity import v3
from keystoneauth1 import session


def get_token_from_keystone(auth_url: str, username: str, password: str, project_name: str = 'admin',
                            user_domain_id: str = 'default', project_domain_id: str = 'default') -> str:
    """
    This function return keystone token.
    :param auth_url: Keystone url
    :param username: Keystone username
    :param password: Keystone password
    :param project_name: Keystone project
    :param user_domain_id: User domain id
    :param project_domain_id: Project domain id

    :rtype: str
    """
    auth = v3.Password(auth_url=auth_url,
                       username=username,
                       password=password,
                       project_name=project_name,
                       user_domain_id=user_domain_id,
                       project_domain_id=project_domain_id)

    sess = session.Session(auth=auth)
    token = sess.get_token()

    return token

