from datetime import datetime
import logging
import threading

from krbticket.command import KrbCommand
from krbticket.config import KrbConfig
from krbticket.updater import KrbTicketUpdater

logger = logging.getLogger(__name__)


class NoCredentialFound(Exception):
    pass


class KrbTicket():

    __instances__ = {}
    __instances_lock__ = threading.Lock()

    def __init__(self, config=None, file=None, principal=None, starting=None, expires=None,
                 service_principal=None, renew_expires=None):

        self.config = config
        self.file = file
        self.principal = principal
        self.starting = starting
        self.expires = expires
        self.service_principal = service_principal
        self.renew_expires = renew_expires
        self._updater = None
        self._updater_lock = threading.RLock()

    def updater_start(self, interval=KrbTicketUpdater.DEFAULT_INTERVAL):
        with self._updater_lock:
            updater = self.updater(interval=interval)
            updater.start()

    def updater(self, interval=KrbTicketUpdater.DEFAULT_INTERVAL):
        with self._updater_lock:
            if not self._updater:
                self._updater = self.config.updater_class(self, interval=interval)
        return self._updater

    def maybe_update(self):
        self.reload()

        if self.is_expired():
            if self.is_renewalable():
                self.renewal()
            else:
                self.reinit()

    def update(self, **kwargs):
        self.__dict__.update(**kwargs)

    def renewal(self):
        logger.info("Renewing ticket for {}...".format(self.principal))
        KrbCommand.renewal(self.config)
        self.reload()

    def reinit(self):
        logger.info("Reinitialize ticket for {}...".format(self.principal))
        KrbCommand.kinit(self.config)
        self.reload()

    def reload(self):
        logger.debug(
            "Reloading ticket attributes from {}...".format(self.file))
        KrbTicket.get_by_config(self.config)
        logger.debug(
            "Reloaded ticket attributes: {}...".format(self))

    def is_expired(self):
        return self.expires < self.config.renewal_threshold + datetime.now()

    def is_renewalable(self):
        if self.renew_expires:
            return self.renew_expires > self.config.renewal_threshold + datetime.now()
        else:
            return False

    def __str__(self):
        super_str = super(KrbTicket, self).__str__()
        return "{}: file={}, principal={}, starting={}, expires={}," \
               " service_principal={}, renew_expires={}" \
               .format(super_str, self.file, self.principal, self.starting,
                       self.expires, self.service_principal, self.renew_expires)

    @staticmethod
    def get_instance(**kwargs):
        ccache_name = kwargs.get('config').ccache_name
        with KrbTicket.__instances_lock__:
            if ccache_name not in KrbTicket.__instances__:
                KrbTicket.__instances__.update({ccache_name: KrbTicket(**kwargs)})
        ticket = KrbTicket.__instances__.get(ccache_name)
        ticket.update(**kwargs)
        return ticket

    @staticmethod
    def cache_exists(config):
        return KrbCommand.cache_exists(config)

    @staticmethod
    def init(principal, keytab=None, **kwargs):
        config = KrbConfig(principal=principal, keytab=keytab, **kwargs)
        return KrbTicket.init_by_config(config)

    @staticmethod
    def init_by_config(config):
        KrbCommand.kinit(config)
        return KrbTicket.get_by_config(config)

    @staticmethod
    def get_or_init(principal, keytab=None, **kwargs):
        config = KrbConfig(principal=principal, keytab=keytab, **kwargs)
        try:
            return KrbTicket.get_by_config(config)
        except NoCredentialFound:
            return KrbTicket.init_by_config(config)

    @staticmethod
    def get(principal, keytab=None, **kwargs):
        config = KrbConfig(principal=principal, keytab=keytab, **kwargs)
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
            return KrbTicket.get_instance(config=config)

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

        return KrbTicket.get_instance(
            config=config,
            file=file,
            principal=principal,
            starting=parseDatetime(starting),
            expires=parseDatetime(expires),
            service_principal=service_principal,
            renew_expires=parseDatetime(renew_expires))

    @staticmethod
    def _destroy():
        """
        destroy internal ticket registry

        stop all updaters belonging to a ticket registered in registry, and remove all entiries
        """
        with KrbTicket.__instances_lock__:
            for (key, ticket) in KrbTicket.__instances__.items():
                ticket.updater().stop()
                KrbCommand.kdestroy(ticket.config)
            KrbTicket.__instances__ = {}
