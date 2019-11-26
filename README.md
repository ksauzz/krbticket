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

### Retry

krbticket supports retry feature utilizing [retrying](https://github.com/rholder/retrying) which provides various retry strategy. To change the behavior, pass the options using `retry_options` of KrbConfig. The dafault values are:

- wait_exponential_multiplier = 1000
- wait_exponential_multiplier = 30000
- stop_max_attempt_number = 10

```
from krbticket import KrbTicket

retry_options = {
  'wait_exponential_multiplier': 1000,
  'wait_exponential_multiplier': 10000,
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
