FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      python3-pip \
      python3-setuptools \
      gettext \
      krb5-user && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY README.md setup.py entrypoint.sh pytest.ini /app/
COPY krbticket /app/krbticket
COPY tests /app/tests
COPY tests/conf/krb5.conf.tmpl tests/conf/krb5.keytab /etc/
RUN chmod 755 /app/entrypoint.sh

ENV KRB5_HOST localhost

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["pytest"]
