from krbticket import KrbTicket, KrbCommand, NoCredentialFound
from helper import *
from datetime import datetime
import os
import subprocess


def test_init(config):
    KrbCommand.kdestroy(config)
    KrbTicket.init(DEFAULT_PRINCIPAL, DEFAULT_KEYTAB)


def test_get_or_init(config):
    KrbCommand.kdestroy(config)
    ticket0 = KrbTicket.get_or_init(DEFAULT_PRINCIPAL, DEFAULT_KEYTAB)
    ticket1 = KrbTicket.get_or_init(DEFAULT_PRINCIPAL, DEFAULT_KEYTAB)
    assert_ticket(ticket0, ticket1)


def test_init_with_keytab_env(config):
    KrbCommand.kdestroy(config)
    os.environ['KRB5_KTNAME'] = config.keytab
    config.keytab = None
    KrbTicket.init(DEFAULT_PRINCIPAL)
    del os.environ['KRB5_KTNAME']
    assert not os.environ.get('KRB5_KTNAME')


def test_init_without_keytab_env(config):
    KrbCommand.kdestroy(config)
    assert not os.environ.get('KRB5_KTNAME')
    retry_options = {
            'wait_exponential_multiplier': 100,
            'wait_exponential_max': 1000,
            'stop_max_attempt_number': 1 }
    config.keytab = None
    try:
        KrbTicket.init(DEFAULT_PRINCIPAL, retry_options=retry_options)
        pytest.fail()
    except subprocess.CalledProcessError:
        pass


def test_init_with_config(config):
    KrbCommand.kdestroy(config)
    ticket1 = KrbTicket.init_by_config(config)
    ticket2 = KrbTicket.init(
            DEFAULT_PRINCIPAL,
            DEFAULT_KEYTAB,
            renewal_threshold=timedelta(seconds=DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC),
            ticket_lifetime=DEFAULT_TICKET_LIFETIME,
            ticket_renewable_lifetime=DEFAULT_TICKET_RENEWABLE_LIFETIME,
            retry_options={
                'wait_exponential_multiplier': 100,
                'wait_exponential_max': 1000,
                'stop_max_attempt_number': 3})
    assert_ticket(ticket1, ticket2)


def test_get(config):
    KrbCommand.kdestroy(config)
    with pytest.raises(NoCredentialFound):
        KrbTicket.get(DEFAULT_PRINCIPAL, DEFAULT_KEYTAB)

    assert_ticket(
        KrbTicket.init_by_config(config),
        KrbTicket.get(
            DEFAULT_PRINCIPAL,
            DEFAULT_KEYTAB,
            renewal_threshold=timedelta(seconds=DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC),
            ticket_lifetime=DEFAULT_TICKET_LIFETIME,
            ticket_renewable_lifetime=DEFAULT_TICKET_RENEWABLE_LIFETIME,
            retry_options={
                'wait_exponential_multiplier': 100,
                'wait_exponential_max': 1000,
                'stop_max_attempt_number': 3}))


def test_ticket(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    assert ticket.config == config
    assert ticket.file
    assert ticket.principal == 'user@EXAMPLE.COM'
    assert ticket.starting
    assert ticket.expires
    assert ticket.service_principal
    assert ticket.renew_expires


def test_parse_klist_output(config):
    output = """
Ticket cache: FILE:/tmp/krb5cc_1000
Default principal: user@EXAMPLE.COM

Valid starting     Expires            Service principal
11/22/19 00:23:10  11/22/19 00:23:12  krbtgt/EXAMPLE.COM@EXAMPLE.COM
        renew until 12/20/19 00:23:10
""".strip()
    ticket = KrbTicket.parse_from_klist(config, output)
    assert ticket.principal == 'user@EXAMPLE.COM'
    assert ticket.service_principal == 'krbtgt/EXAMPLE.COM@EXAMPLE.COM'
    assert ticket.starting == datetime(2019, 11, 22, 0, 23, 10)
    assert ticket.expires == datetime(2019, 11, 22, 0, 23, 12)
    assert ticket.renew_expires == datetime(2019, 12, 20, 0, 23, 10)
