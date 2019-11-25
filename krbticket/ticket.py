import os
from datetime import datetime
import threading
import time
import logging

from .config import KrbConfig
from .command import KrbCommand


class NoCredentialFound(Exception):
    pass


class KrbTicketUpdater(threading.Thread):
    DEFAULT_INTERVAL = 60 * 10

    def __init__(self, ticket, interval=DEFAULT_INTERVAL):
        super(KrbTicketUpdater, self).__init__()

        self.ticket = ticket
        self.interval = interval
        self.stop_event = threading.Event()
        self.daemon = True

    def run(self):
        logging.info("Ticket updater start...")
        while True:
            if self.stop_event.is_set():
                return

            logging.debug("Trying to update ticket...")
            self.ticket.maybe_update()
            time.sleep(self.interval)

    def stop(self):
        logging.debug("Stopping ticket updater...")
        self.stop_event.set()


class KrbTicket():
    def __init__(self, config=None, file=None, principal=None, starting=None, expires=None,
                 service_principal=None, renew_expires=None):

        self.config = config
        self.file = file
        self.principal = principal
        self.starting = starting
        self.expires = expires
        self.service_principal = service_principal
        self.renew_expires = renew_expires

    def updater_start(self, interval=KrbTicketUpdater.DEFAULT_INTERVAL):
        self.updater(interval=interval).start()

    def updater(self, interval=KrbTicketUpdater.DEFAULT_INTERVAL):
        return KrbTicketUpdater(self, interval=interval)

    def maybe_update(self):
        self.reload()

        if self.need_reinit():
            self.reinit()

        elif self.need_renewal():
            self.renewal()

    def renewal(self):
        logging.info("Renewing ticket for {}...".format(self.principal))
        KrbCommand.renewal(self.config)
        self.reload()

    def reinit(self):
        logging.info("Reinitialize ticket for {}...".format(self.principal))
        KrbCommand.kinit(self.config)
        self.reload()

    def reload(self):
        logging.debug(
            "Reloading ticket attributes from {}...".format(self.file))

        new_ticket = KrbTicket.get_by_config(self.config)
        self.file = new_ticket.file
        self.principal = new_ticket.principal
        self.starting = new_ticket.starting
        self.expires = new_ticket.expires
        self.service_principal = new_ticket.service_principal
        self.renew_expires = new_ticket.renew_expires
        logging.debug(
            "Reloaded ticket attributes: {}...".format(self))

    def need_renewal(self):
        return self.expires < self.config.renewal_threshold + datetime.now()

    def need_reinit(self):
        if self.renew_expires:
            return self.renew_expires < self.config.renewal_threshold + datetime.now()
        else:
            return self.need_renewal()


    def __str__(self):
        super_str = super(KrbTicket, self).__str__()
        return "{}: file={}, principal={}, starting={}, expires={}," \
               " service_principal={}, renew_expires={}" \
               .format(super_str, self.file, self.principal, self.starting,
                       self.expires, self.service_principal, self.renew_expires)


    @staticmethod
    def cache_exists(config):
        return os.path.isfile(config.ccache_name)

    @staticmethod
    def init(principal, keytab, **kwargs):
        config = KrbConfig(principal, keytab, **kwargs)
        return KrbTicket.init_by_config(config)

    @staticmethod
    def init_by_config(config):
        KrbCommand.kinit(config)
        return KrbTicket.get_by_config(config)

    @staticmethod
    def get(principal, keytab, **kwargs):
        config = KrbConfig(principal, keytab, **kwargs)
        return KrbTicket.get_by_config(config)

    @staticmethod
    def get_by_config(config):
        if KrbTicket.cache_exists(config):
            return KrbTicket.parse_from_klist(config, KrbCommand.klist(config))
        else:
            raise NoCredentialFound()

    @staticmethod
    def parse_from_klist(config, output):
        if not output:
            return KrbTicket(config)

        lines = output.splitlines()
        file = lines[0].split(':')[2]
        principal = lines[1].split(':')[1].strip()
        starting, expires, service_principal = lines[4].strip().split('  ')
        if len(lines) > 5:
            renew_expires = lines[5].strip().replace('renew until ', '')
        else:
            renew_expires = None

        def parseDatetime(str):
            if str:
                return datetime.strptime(str, '%m/%d/%y %H:%M:%S')

        return KrbTicket(
            config,
            file,
            principal,
            parseDatetime(starting),
            parseDatetime(expires),
            service_principal,
            parseDatetime(renew_expires))
