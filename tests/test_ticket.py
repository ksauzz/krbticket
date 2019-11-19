from krbticket import KrbTicket, KrbCommand
from krbticket.ticket import NoCredentialFound
from helper import *
import time


def test_init(config):
    KrbCommand.kdestroy(config)
    ticket1 = KrbTicket.init_by_config(config)
    ticket2 = KrbTicket.init(DEFAULT_PRINCIPAL, DEFAULT_KEYTAB)
    assert ticket1.principal == ticket2.principal
    assert ticket1.file == ticket2.file


def test_get(config):
    KrbCommand.kdestroy(config)
    with pytest.raises(NoCredentialFound):
        KrbTicket.get(DEFAULT_PRINCIPAL, DEFAULT_KEYTAB)

    assert_ticket(
            KrbTicket.init_by_config(config),
            KrbTicket.get(DEFAULT_KEYTAB, DEFAULT_PRINCIPAL))


def test_ticket(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    assert ticket.config == config
    assert ticket.file
    assert ticket.principal == 'user@EXAMPLE.COM'
    assert ticket.starting
    assert ticket.expires
    assert ticket.service_principal


def test_updater(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    updater = ticket.updater(interval=1)
    updater.start()
    updater.stop()
    time.sleep(2)
    assert not updater.is_alive()


def test_renewal(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    starting = ticket.starting
    expires = ticket.expires
    updater = ticket.updater(interval=1)
    updater.start()
    time.sleep(2)
    updater.stop()
    assert ticket.starting > starting
    assert ticket.expires > expires
