from datetime import timedelta
import logging
import multiprocessing
import os

logger = logging.getLogger(__name__)


class KrbConfig():
    from krbticket.updater import SimpleKrbTicketUpdater

    def __init__(self, principal=None, keytab=None, kinit_bin="kinit",
                 klist_bin="klist", kdestroy_bin="kdestroy",
                 renewal_threshold=timedelta(minutes=30),
                 ticket_lifetime=None,
                 ticket_renewable_lifetime=None,
                 ccache_name=None,
                 updater_class=SimpleKrbTicketUpdater,
                 retry_options={
                     'wait_exponential_multiplier': 1000,
                     'wait_exponential_max': 30000,
                     'stop_max_attempt_number': 10}):
        self.principal = principal
        self.keytab = keytab
        self.kinit_bin = kinit_bin
        self.klist_bin = klist_bin
        self.kdestroy_bin = kdestroy_bin
        self.renewal_threshold = renewal_threshold
        self.ticket_lifetime = ticket_lifetime
        self.ticket_renewable_lifetime = ticket_renewable_lifetime
        self.updater_class = updater_class
        self.retry_options = retry_options
        self.ccache_name = ccache_name if ccache_name else self._ccache_name()
        self.ccache_lockfile = '{}.krbticket.lock'.format(self.ccache_name)
        self.ccache_cmd_lockfile = '{}.krbticket.cmd.lock'.format(self.ccache_name)

    def __str__(self):
        super_str = super(KrbConfig, self).__str__()
        return "{}: principal={}, keytab={}, kinit_bin={}," \
               " klist_bin={}, kdestroy_bin={}, " \
               " renewal_threshold={}, ticket_lifetime={}, " \
               " ticket_renewable_lifetime={}, " \
               " retry_options={}, ccache_name={}, " \
               " updater_class={}" \
               .format(super_str, self.principal, self.keytab, self.kinit_bin,
                       self.klist_bin, self.kdestroy_bin,
                       self.renewal_threshold, self.ticket_lifetime,
                       self.ticket_renewable_lifetime,
                       self.retry_options, self.ccache_name,
                       self.updater_class)

    def _ccache_name(self):
        if self.updater_class.use_per_process_ccache():
            return self._per_process_ccache_name()
        else:
            return self._default_ccache_name()

    def _is_main_process(self):
        return multiprocessing.current_process().name == 'MainProcess'

    def _default_ccache_name(self):
        return os.environ.get('KRB5CCNAME', '/tmp/krb5cc_{}'.format(os.getuid()))

    def _per_process_ccache_name(self):
        if self._is_main_process():
            return self._default_ccache_name()

        new_ccname = "/tmp/krb5cc_{}_{}".format(os.getuid(), os.getpid())
        # Update KRB5CCNAME for kinit
        os.environ['KRB5CCNAME'] = new_ccname
        logger.info("env KRB5CCNAME is updated to '{}' for multiprocessing".format(new_ccname))

        return os.environ.get('KRB5CCNAME')
