# ptah api

# uri
from ptah.uri import resolve
from ptah.uri import resolver
from ptah.uri import register_uri_resolver
from ptah.uri import extract_uri_schema
from ptah.uri import UriFactory

# security
from ptah.authentication import authService
from ptah.authentication import SUPERUSER_URI

from ptah.authentication import auth_checker
from ptah.authentication import auth_provider
from ptah.authentication import register_auth_provider

from ptah.authentication import search_principals
from ptah.authentication import principal_searcher
from ptah.authentication import register_principal_searcher

# acl
from ptah.security import ACL
from ptah.security import ACLsProperty
from ptah.security import get_acls
from ptah.interfaces import IACLsAware

# role
from ptah.security import Role
from ptah.security import get_roles
from ptah.security import get_local_roles
from ptah.interfaces import IOwnersAware
from ptah.interfaces import ILocalRolesAware

# permission
from ptah.security import Permission
from ptah.security import get_permissions
from ptah.security import check_permission

# default roles and permissions
from ptah.security import Everyone
from ptah.security import Authenticated
from ptah.security import Owner
from ptah.security import DEFAULT_ACL
from ptah.security import NOT_ALLOWED
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import NO_PERMISSION_REQUIRED

# password tool
from ptah.password import pwd_tool
from ptah.password import password_changer
from ptah.password import PWD_CONFIG

# formatter
from ptah.formatter import format

# rest api
from ptah.rest import RestService
from ptah.rest import enable_rest_api

# events
from ptah import events

# mail templates
from ptah import mail
from ptah.settings import MAIL

# pagination
from ptah.util import Pagination

# thread local data
from ptah.util import tldata

# ReST renderer
from ptah.rst import rst_to_html

# sqlalchemy utils
from ptah.sqla import QueryFreezer
from ptah.sqla import JsonDictType
from ptah.sqla import JsonListType
from ptah.sqla import generate_fieldset
from ptah.sqla import build_sqla_fieldset

# simple ui actions
from ptah.uiactions import uiaction
from ptah.uiactions import list_uiactions

# manage
from ptah import manage

# cms
from ptah import cms


# pyramid include
def includeme(config):
    config.add_directive('ptah_initialize', ptah_initialize)

    # ptah.config directives
    from ptah.config.api import get_cfg_storage_imp
    config.add_directive(
        'get_cfg_storage', get_cfg_storage_imp)

    # ptah.config.settings directives
    from ptah.config.settings import pyramid_get_settings
    config.add_directive(
        'ptah_get_settings', pyramid_get_settings)

    # ptah.authentication directives
    from ptah import authentication
    config.add_directive(
        'ptah_auth_checker', authentication.pyramid_auth_checker)
    config.add_directive(
        'ptah_auth_provider', authentication.pyramid_auth_provider)
    config.add_directive(
        'ptah_principal_searcher', authentication.pyramid_principal_searcher)

    # ptah.uri directives
    from ptah import uri
    config.add_directive(
        'ptah_uri_resolver', uri.pyramid_uri_resolver)

    # ptah.password directives
    from ptah import password
    config.add_directive(
        'ptah_password_changer', password.pyramid_password_changer)


def make_wsgi_app(global_settings, **settings):
    """ Create wsgi application, this function initialize
    `ptah` and sends :py:class:`AppInitialized` event.
    It is possible to use this function as entry point for paster based
    deployment::

      [app:myapp]
      use = egg:ptah#app

    """
    import sys
    import ptah
    from pyramid.config import Configurator

    authService.set_userid(SUPERUSER_URI)

    # configuration
    config = Configurator(settings=settings)

    # initialization
    packages = settings.get('packages', None)
    autoinclude = settings.get('autoinclude', True)
    try:
        ptah_initialize(config, packages, autoinclude)
    except Exception as e:
        if isinstance(e, ptah.config.StopException):
            print e.print_tb()

        sys.exit(0)
        return

    config.commit()

    # create wsgi app
    return config.make_wsgi_app()


# initialize ptah
def ptah_initialize(configurator, packages=None, autoinclude=False):
    """ Initialize ptah packages.
    Load all ptah packages and intialize ptah settings system.

    This function automatically called by :py:func:`make_wsgi_app` function.
    """
    import ptah
    import sqlahelper
    import transaction
    from pyramid.exceptions import  ConfigurationExecutionError

    configurator.include('ptah')
    configurator.include('pyramid_tm')
    configurator.begin()

    try:
        settings = configurator.registry.settings

        # exclude
        excludes = []
        if 'ptah.excludes' in settings:
            excludes.extend(s.strip()
                            for s in settings['ptah.excludes'].split())

        # load packages
        ptah.config.initialize(
            configurator, packages, excludes, autoinclude, initsettings=True)

        configurator.commit()

        # create sql tables
        Base = sqlahelper.get_base()
        Base.metadata.create_all()

        # send AppStarting event
        ptah.config.start(configurator)

        # commit possible transaction
        transaction.commit()
    except Exception as e:
        if isinstance(e, ConfigurationExecutionError):
            e = e.evalue

        if not isinstance(e, ptah.config.StopException):
            ptah.config.shutdown()
            e = ptah.config.StopException(e)
            raise e

        ptah.config.shutdown()
        raise e
    finally:
        configurator.end()
