"""Optional LDAP / Active Directory authentication wiring.

This module is imported from base settings only when LDAP_ENABLED=True so
that the django-auth-ldap dependency stays inert for the default JWT setup
(cloude.md module 1: SSO via Windows AD over LDAP).

To activate:
  1. Set LDAP_ENABLED=True and the LDAP_* vars in .env
  2. Ensure django-auth-ldap is installed (it is, see requirements.txt)
"""
import ldap  # noqa: F401  (provided by python-ldap, pulled in by django-auth-ldap)
from decouple import config
from django_auth_ldap.config import GroupOfNamesType, LDAPSearch

AUTH_LDAP_SERVER_URI = config("LDAP_SERVER_URI", default="")
AUTH_LDAP_BIND_DN = config("LDAP_BIND_DN", default="")
AUTH_LDAP_BIND_PASSWORD = config("LDAP_BIND_PASSWORD", default="")

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    config("LDAP_USER_SEARCH_BASE", default=""),
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)",
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    config("LDAP_GROUP_SEARCH_BASE", default=""),
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)",
)
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")

# Map AD attributes onto the custom user model.
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

# Create/keep a local mirror row so RBAC/role still applies.
AUTH_LDAP_ALWAYS_UPDATE_USER = True

# Authentication backends: try LDAP first, then fall back to local accounts.
AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
]
