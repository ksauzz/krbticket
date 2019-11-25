from datetime import timedelta
import multiprocessing
import os


class KrbConfig():
    def __init__(self, principal=None, keytab=None, kinit_bin="kinit",
                 klist_bin="klist", kdestroy_bin="kdestroy",
                 renewal_threshold=timedelta(minutes=30),
                 ticket_lifetime=None,
                 ticket_renewable_lifetime=None,
                 ccache_name=None,
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
        self.retry_options = retry_options
        self.ccache_name = ccache_name if ccache_name else self._ccache_name()


    def __str__(self):
        super_str = super(KrbConfig, self).__str__()
        return "{}: principal={}, keytab={}, kinit_bin={}," \
               " klist_bin={}, kdestroy_bin={}, " \
               " renewal_threshold={}, ticket_lifetime={}, " \
               " retry_options={}, ccache_name={}, " \
               .format(super_str, self.principal, self.keytab, self.kinit_bin, self.klist_bin, self.kdestroy_bin, self.renewal_threshold, self.ticket_lifetime, self.ticket_renewable_lifetime, self.retry_options, self.ccache_name)


    def _ccache_name(self):
        if multiprocessing.current_process().name == 'MainProcess':
            if os.environ.get('KRB5CCNAME'):
                return os.environ.get('KRB5CCNAME')
            else:
                return "/tmp/krb5cc_{}".format(os.getuid())
        else:
            # For multiprocess application. e.g. gunicorn
            return "/tmp/krb5cc_{}_{}".format(os.getuid(), os.getpid())
