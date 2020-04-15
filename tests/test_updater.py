from krbticket import KrbTicket, KrbCommand
from krbticket import SimpleKrbTicketUpdater, SingleProcessKrbTicketUpdater, MultiProcessKrbTicketUpdater
from helper import *
import time
import pytest
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


def teardown_function(function):
    KrbTicket._destroy()


def test_updater(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    updater = ticket.updater(interval=1)
    updater.start()
    assert updater.is_alive()
    updater.stop()
    time.sleep(2)
    assert not updater.is_alive()


def test_reuse_updater(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    updater = ticket.updater(interval=1)
    updater.start()
    assert updater.is_alive()
    updater.stop()
    time.sleep(2)
    assert not updater.is_alive()
    updater.start()
    assert not updater.is_alive()


def test_updater_start(config):
    KrbCommand.kdestroy(config)
    ticket = KrbTicket.init_by_config(config)
    ticket.updater_start(interval=1)
    assert ticket.updater().is_alive()
    ticket.updater().stop()
    time.sleep(2)
    assert not ticket.updater().is_alive()

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


@pytest.mark.parametrize('config_str', [
    'default_config(updater_class=SimpleKrbTicketUpdater)',
    'default_config(updater_class=MultiProcessKrbTicketUpdater)',
    'default_config(updater_class=SingleProcessKrbTicketUpdater)'
])
def test_single_thread_updater_in_multithreading(config_str, caplog):
    KrbCommand.kdestroy(eval(config_str))
    ticket = KrbTicket.init_by_config(eval(config_str))
    updater = ticket.updater(interval=0.5)
    updater.start()

    def run():
        t_ticket = KrbTicket.get_by_config(eval(config_str))
        t_updater = t_ticket.updater(interval=0.5)

        assert updater == t_updater
        assert t_updater.is_alive()

        t_updater.start()
        assert ticket == t_ticket
        assert_ticket(ticket, t_ticket)

        time.sleep(3)


    executor = ThreadPoolExecutor(max_workers=10)
    for future in [executor.submit(run) for i in range(10)]:
        future.result()


@pytest.mark.parametrize('config_str', [
    'default_config(updater_class=SimpleKrbTicketUpdater)',
    'default_config(updater_class=MultiProcessKrbTicketUpdater)',
    'default_config(updater_class=SingleProcessKrbTicketUpdater)'
])
def test_skip_subsequent_updater_start_with_multithreading(config_str, caplog):
    KrbCommand.kdestroy(eval(config_str))
    KrbTicket.init_by_config(eval(config_str))

    # Subsequent updater.start should be skipped.
    executor = ThreadPoolExecutor(max_workers=5)
    for future in [executor.submit(_updater_run, eval(config_str)) for i in range(10)]:
        future.result()


@pytest.mark.parametrize('config_str', [
    'default_config(updater_class=SimpleKrbTicketUpdater)',
    'default_config(updater_class=MultiProcessKrbTicketUpdater)',
    'default_config(updater_class=SingleProcessKrbTicketUpdater)'
])
def test_skip_subsequent_updater_start_with_multiprocessing(config_str, caplog):
    KrbCommand.kdestroy(eval(config_str))
    KrbTicket.init_by_config(eval(config_str))
    # Subsequent updater.start should be skipped.
    executor = ProcessPoolExecutor(max_workers=5)
    for future in [executor.submit(_updater_run, eval(config_str)) for i in range(10)]:
        future.result()


def _updater_run(config):
    ticket = KrbTicket.init_by_config(config)
    updater = ticket.updater(interval=0.5)
    updater.start()
    updater.start()
