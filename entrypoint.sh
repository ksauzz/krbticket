#!/bin/bash
set -eu

envsubst < /etc/krb5.conf.tmpl > /etc/krb5.conf
pip3 install -e '.[test]'

exec "$@"
