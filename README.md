# Kerberos Ticket Manager

Simple kinit wrapper to update Kerberos ticket periodically for long running application.

## Getting Started

Periodical kerberos ticket update

```
from krbticket import KrbTicket

ticket = KrbTicket.init("<principal>", "<keytab path>")
ticket.updater_start()
```
