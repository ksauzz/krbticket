# Kerberos Ticket Manager

Simple kinit wrapper to update Kerberos ticket periodically for long running application.

## Getting Started

Periodical kerberos ticket update

```
from krbticket import KrbTicket

ticket = KrbTicket.init("<principal>", "<keytab path>")
ticket.updater_start()
```

## Test

```
docker run --rm -p 88:88 ksauzz/docker-krb5:0.0.1
KRB5_CONFIG=tests/conf/krb5.conf.local pytest
```
