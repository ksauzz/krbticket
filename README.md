# Kerberos Ticket Manager

Simple kinit wrapper for updating Kerberos ticket periodically

## Getting Started

Periodical kerberos ticket update

```
from krbticket import KrbTicket

ticket = KrbTicket.init("<principal>", "<keytab path>")
ticket.updater_start()
```
