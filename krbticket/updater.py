import logging
import threading
import time

import fasteners

logger = logging.getLogger(__name__)


class KrbTicketUpdater(threading.Thread):
    DEFAULT_INTERVAL = 60 * 10

    def __init__(self, ticket, interval=DEFAULT_INTERVAL):
        super(KrbTicketUpdater, self).__init__()

        self.ticket = ticket
        self.interval = interval
        self.stop_event = threading.Event()
        self.daemon = True
        self.start_lock = threading.Lock()

    def run(self):
        logger.info("{} start...".format(self.__class__.__name__))
        while True:
            if self.stop_event.is_set():
                return

            logger.debug("Trying to update ticket...")
            self.ticket.maybe_update()
            time.sleep(self.interval)

    def start(self):
        with self.start_lock:
            if self.is_alive():
                logger.debug("Skipping Thread.start() since it already started...")
                return

            if self.stop_event.is_set():
                logger.debug("Skipping Thread.start() since it already stopped...")
                return

            super().start()

    @staticmethod
    def use_per_process_ccache():
        raise NotImplementedError

    def stop(self):
        logger.debug("Stopping ticket updater...")
        self.stop_event.set()


class SimpleKrbTicketUpdater(KrbTicketUpdater):
    """
    KrbTicketUpdater w/o exclusion control

    Using this with multiprocessing, child processes uses dedicated ccache file
    """
    @staticmethod
    def use_per_process_ccache():
        return True


class MultiProcessKrbTicketUpdater(KrbTicketUpdater):
    """
    Multiprocess KrbTicket Updater

    KrbTicketUpdater w/ exclusive lock for a ccache
    """
    @staticmethod
    def use_per_process_ccache():
        return False


class SingleProcessKrbTicketUpdater(KrbTicketUpdater):
    """
    Singleprocess KrbTicket Updater

    Single Process KrbTicketUpdater on the system.
    Multiple updaters can start, but they immediately stops if a updater is already running on the system.
    """
    def start(self):
        lock = fasteners.InterProcessLock(self.ticket.config.ccache_lockfile)
        got_lock = lock.acquire(blocking=False)
        if not got_lock:
            logger.debug("Another updater is detected. Stopping ticket updater...")
            return

        logger.debug("Got lock: {}...".format(self.ticket.config.ccache_lockfile))
        try:
            super().start()
        finally:
            if got_lock:
                lock.release()
                logger.debug("Released lock: {}...".format(self.ticket.config.ccache_lockfile))

    @staticmethod
    def use_per_process_ccache():
        return False
