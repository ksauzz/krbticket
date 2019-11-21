from krbticket import KrbConfig
import os


def test_ccache_name():
    assert KrbConfig().ccache_name == '/tmp/krb5cc_{}'.format(os.getuid())
    assert KrbConfig(ccache_name="/tmp/hoge").ccache_name == '/tmp/hoge'
    os.environ['KRB5CCNAME'] = '/tmp/env_krb5cc'
    assert KrbConfig().ccache_name == '/tmp/env_krb5cc'
    del os.environ['KRB5CCNAME']
