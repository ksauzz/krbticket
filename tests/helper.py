import pytest
from krbticket import KrbConfig
from datetime import timedelta
import os

DEFAULT_PRINCIPAL = 'user@EXAMPLE.COM'
DEFAULT_KEYTAB = './tests/conf/krb5.keytab'
DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC = 1
DEFAULT_TICKET_LIFETIME_SEC = 4
DEFAULT_TICKET_LIFETIME = '{}s'.format(DEFAULT_TICKET_LIFETIME_SEC)
DEFAULT_TICKET_RENEWABLE_LIFETIME_SEC = 8
DEFAULT_TICKET_RENEWABLE_LIFETIME = '{}s'.format(DEFAULT_TICKET_RENEWABLE_LIFETIME_SEC)
DEFAULT_CCACHE_NAME = '/tmp/krb5cc_{}'.format(os.getuid())


def assert_ticket(t1, t2):
    assert t1.principal == t2.principal
    assert t1.file == t2.file
    assert t1.starting == t2.starting
    assert t1.expires == t2.expires
    assert t1.service_principal == t2.service_principal
    assert_config(t1.config, t2.config)


def assert_config(c1, c2):
    print(c1)
    print(c2)
    assert c1.principal == c2.principal
    assert c1.keytab == c2.keytab
    assert c1.kinit_bin == c2.kinit_bin
    assert c1.klist_bin == c2.klist_bin
    assert c1.kdestroy_bin == c2.kdestroy_bin
    assert c1.renewal_threshold == c2.renewal_threshold
    assert c1.ticket_lifetime == c2.ticket_lifetime
    assert c1.ticket_renewable_lifetime == c2.ticket_renewable_lifetime
    assert c1.ccache_name == c2.ccache_name


def default_config(**kwargs):
    default_options = {
        'principal': DEFAULT_PRINCIPAL,
        'keytab': DEFAULT_KEYTAB,
        'renewal_threshold': timedelta(seconds=DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC),
        'ticket_lifetime': DEFAULT_TICKET_LIFETIME,
        'ticket_renewable_lifetime': DEFAULT_TICKET_RENEWABLE_LIFETIME,
        'retry_options': {
            'wait_exponential_multiplier': 100,
            'wait_exponential_max': 1000,
            'stop_max_attempt_number': 3}
        }
    return KrbConfig(**{**default_options, **kwargs})


@pytest.fixture
def config():
    return default_config()
