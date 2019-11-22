import pytest
from krbticket import KrbConfig
from datetime import timedelta

DEFAULT_PRINCIPAL = 'user@EXAMPLE.COM'
DEFAULT_KEYTAB = './tests/conf/krb5.keytab'
DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC = 1
DEFAULT_TICKET_LIFETIME = '2s'
DEFAULT_TICKET_RENEWABLE_LIFETIME = '4s'


def assert_ticket(t1, t2):
    assert t1.principal == t2.principal
    assert t1.file == t2.file
    assert t1.starting == t2.starting
    assert t1.expires == t2.expires
    assert t1.service_principal == t2.service_principal


def default_config():
    return KrbConfig(
        DEFAULT_PRINCIPAL,
        DEFAULT_KEYTAB,
        renewal_threshold=timedelta(seconds=DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC),
        ticket_lifetime=DEFAULT_TICKET_LIFETIME,
        ticket_renewable_lifetime=DEFAULT_TICKET_RENEWABLE_LIFETIME,
        retry_options={
            'wait_exponential_multiplier': 100,
            'wait_exponential_max': 1000,
            'stop_max_attempt_number': 3})


@pytest.fixture
def config():
    return default_config()
