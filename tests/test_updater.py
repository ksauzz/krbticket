from krbticket import KrbTicket, KrbCommand
from krbticket import SimpleKrbTicketUpdater, SingleProcessKrbTicketUpdater, MultiProcessKrbTicketUpdater
from helper import *
import time
from multiprocessing import Process


def test_updater(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    updater = ticket.updater(interval=1)
    updater.start()
    updater.stop()
    time.sleep(2)
    assert not updater.is_alive()

@pytest.mark.parametrize('config', [
    default_config(updater_class=SimpleKrbTicketUpdater),
    default_config(updater_class=MultiProcessKrbTicketUpdater),
    default_config(updater_class=SingleProcessKrbTicketUpdater)
])
def test_renewal(config):
    """
    This test assumes:
    - 1 sec renewal threshold
    - 4 sec ticket lifetime
    - 8 sed renewal ticket lifetime
    """
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)

    starting = ticket.starting
    expires = ticket.expires
    renew_expires = ticket.renew_expires

    updater = ticket.updater(interval=0.5)
    updater.start()

    # expect ticket renewal
    time.sleep(DEFAULT_TICKET_LIFETIME_SEC + DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC)
    assert ticket.starting > starting
    assert ticket.expires > expires
    assert ticket.renew_expires == renew_expires

    starting = ticket.starting
    expires = ticket.expires

    # expect ticket re-initialize
    time.sleep(DEFAULT_TICKET_RENEWABLE_LIFETIME_SEC - DEFAULT_TICKET_LIFETIME_SEC + DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC)
    assert ticket.starting > starting
    assert ticket.expires > expires
    assert ticket.renew_expires > renew_expires
    updater.stop()

@pytest.mark.parametrize('config_str', [
    'default_config(updater_class=SimpleKrbTicketUpdater)',
    'default_config(updater_class=MultiProcessKrbTicketUpdater)',
    'default_config(updater_class=SingleProcessKrbTicketUpdater)'
])
def test_multiprocessing_renewal(config_str, caplog):
    KrbCommand.kdestroy(eval(config_str))
    ticket = KrbTicket.init_by_config(eval(config_str))

    def run():
        """
        This test assumes:
        - 1 sec renewal threshold
        - 4 sec ticket lifetime
        - 8 sed renewal ticket lifetime
        """

        starting = ticket.starting
        expires = ticket.expires
        renew_expires = ticket.renew_expires

        updater = ticket.updater(interval=0.5)
        updater.start()

        # expect ticket renewal
        time.sleep(DEFAULT_TICKET_LIFETIME_SEC + DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC)
        if 'SingleProcessKrbTicketUpdater' in config_str:
            # needs manual reload since SingleProcessTicketUpdater is stopped
            ticket.reload()
        assert ticket.starting > starting
        assert ticket.expires > expires
        assert ticket.renew_expires == renew_expires

        starting = ticket.starting
        expires = ticket.expires

        # expect ticket re-initialize
        time.sleep(DEFAULT_TICKET_RENEWABLE_LIFETIME_SEC - DEFAULT_TICKET_LIFETIME_SEC + DEFAULT_TICKET_RENEWAL_THRESHOLD_SEC)
        if 'SingleProcessKrbTicketUpdater' in config_str:
            # needs manual reload since SingleProcessTicketUpdater is stopped
            ticket.reload()
        assert ticket.starting > starting
        assert ticket.expires > expires
        assert ticket.renew_expires > renew_expires
        updater.stop()

    processes = [Process(target=run) for i in range(10)]
    for p in processes:
        p.start()

    for p in processes:
        p.join()
        assert not p.exitcode
