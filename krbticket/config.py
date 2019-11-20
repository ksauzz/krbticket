from datetime import timedelta


class KrbConfig():
    def __init__(self, principal=None, keytab=None, kinit_bin="kinit",
                 klist_bin="klist", kdestroy_bin="kdestroy",
                 renewal_threshold=timedelta(minutes=30),
                 ticket_lifetime=None,
                 retry_options={
                     'wait_exponential_multiplier': 1000,
                     'wait_exponential_max': 30000,
                     'stop_max_attempt_number': 10 }):
        self.principal = principal
        self.keytab = keytab
        self.kinit_bin = kinit_bin
        self.klist_bin = klist_bin
        self.kdestroy_bin = kdestroy_bin
        self.renewal_threshold = renewal_threshold
        self.ticket_lifetime = ticket_lifetime
        self.retry_options = retry_options
