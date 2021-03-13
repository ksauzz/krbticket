# Kerberos Ticket Manager

![build status](https://github.com/ksauzz/krbticket/workflows/test/badge.svg)

Simple kinit wrapper to update Kerberos ticket periodically for long running application.

## Getting Started

Periodical kerberos ticket update

```
from krbticket import KrbTicket

ticket = KrbTicket.init("<principal>", "<keytab path>")
ticket.updater_start()
```

If `keytab path` is not specifyed, kinit uses `KRB5_KTNAME` env, or `/etc/krb5.keytab` to find a keytab file. see: kerberos(1) and kinit(1).

### Ticket Updater Strategies

To avoid a credential cache (ccache) corruption by concurrent updates from multiple processes, KrbTicketUpdater has a few update strategies:

- SimpleKrbTicketUpdater: for single updater process, or multiple updaters w/ per process ccache. (default)
- MultiProcessKrbTicketUpdater: for multiple updater processes w/ exclusive file lock
- SingleProcessKrbTicketUpdater: for multiple updater processes w/ exclusive file lock to restrict the number of updater processes to one against the ccache

```
from krbticket import KrbTicket, SingleProcessKrbTicketUpdater

ticket = KrbTicket.init("<principal>", "<keytab path>", updater_class=SingleProcessKrbTicketUpdater)
ticket.updater_start()
```

### Retry

krbticket supports retry feature utilizing [retrying](https://github.com/rholder/retrying) which provides various retry strategy. To change the behavior, pass the options using `retry_options` of KrbConfig. The dafault values are:

- wait_exponential_multiplier = 1000
- wait_exponential_max = 30000
- stop_max_attempt_number = 10

```
from krbticket import KrbTicket

retry_options = {
  'wait_exponential_multiplier': 1000,
  'wait_exponential_max': 10000,
  'stop_max_attempt_number': 5
}
ticket = KrbTicket.init("<principal>", "<keytab path>", retry_options=retry_options)
ticket.updater_start()
```

### Update Interval

TBD

## Test

```
docker run --rm -p 88:88 ksauzz/docker-krb5:0.0.1
pip install -r requirements-test.txt -r requirements.txt
KRB5_CONFIG=tests/conf/krb5.conf.local pytest
```
