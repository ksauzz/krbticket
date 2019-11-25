from krbticket import KrbTicket, KrbCommand
from krbticket.ticket import NoCredentialFound
from helper import *
from datetime import datetime
import time


def test_init(config):
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


def test_updater(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    updater = ticket.updater(interval=1)
    updater.start()
    updater.stop()
    time.sleep(2)
    assert not updater.is_alive()


def test_renewal(config):
    """
    This test assumes:
    - 1 sec renewal threshold
    - 2 sec ticket lifetime
    - 4 sed renewal ticket lifetime
    """
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)

    starting = ticket.starting
    expires = ticket.expires
    renew_expires = ticket.renew_expires

    updater = ticket.updater(interval=0.5)
    updater.start()

    # expect ticket renewal
    time.sleep(2)
    assert ticket.starting > starting
    assert ticket.expires > expires
    assert ticket.renew_expires == renew_expires

    starting = ticket.starting
    expires = ticket.expires

    # expect ticket re-initialize
    time.sleep(2)
    assert ticket.starting > starting
    assert ticket.expires > expires
    assert ticket.renew_expires > renew_expires
    updater.stop()


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
