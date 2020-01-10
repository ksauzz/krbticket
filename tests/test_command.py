from krbticket import KrbConfig, KrbCommand
from krbticket import MultiProcessKrbTicketUpdater
from helper import *
import os
import subprocess
from multiprocessing import Process
import pytest


def _test_commands(config):
    KrbCommand.kdestroy(config)
    KrbCommand.kinit(config)
    KrbCommand.renewal(config)
    KrbCommand.klist(config)
    KrbCommand.kdestroy(config)


def test_commands(config):
    _test_commands(config)


def test_commands_with_keytab_env(config):
    os.environ['KRB5_KTNAME'] = config.keytab
    config.keytab = None
    _test_commands(config)
    del os.environ['KRB5_KTNAME']
    assert not os.environ.get('KRB5_KTNAME')


def test_commands_without_keytab_env(config):
    assert not os.environ.get('KRB5_KTNAME')
    config.retry_options={
            'wait_exponential_multiplier': 100,
            'wait_exponential_max': 1000,
            'stop_max_attempt_number': 1}
    config.keytab = None
    try:
        _test_commands(config)
        pytest.fail()
    except subprocess.CalledProcessError:
        pass


def test_multiprocessing_with_per_process_ccache(config):
    KrbCommand.kdestroy(config)

    def run():
        conf = default_config()
        assert conf.ccache_name != config.ccache_name
        assert os.environ.get('KRB5CCNAME') == conf.ccache_name
        # check if KRB5CCNAME is recognized kerberos commands
        conf.ccache_name = None
        _test_commands(conf)

    processes = [Process(target=run) for i in range(10)]
    for p in processes:
        p.start()

    for p in processes:
        p.join()
        assert not p.exitcode


def test_multiprocessing_without_per_process_ccache():
    config = default_config(updater_class=MultiProcessKrbTicketUpdater)
    KrbCommand.kdestroy(config)

    def run():
        conf = default_config(updater_class=MultiProcessKrbTicketUpdater)
        assert conf.ccache_name == config.ccache_name
        assert not os.environ.get('KRB5CCNAME')

    processes = [Process(target=run) for i in range(10)]
    for p in processes:
        p.start()

    for p in processes:
        p.join()
        assert not p.exitcode


def test_retry(config, mocker):
    KrbCommand.kdestroy(config)

    raise_exception_twice = [
        subprocess.CalledProcessError(1, ['kinit']),
        subprocess.CalledProcessError(1, ['kinit']),
        None]
    patcher = mocker.patch('subprocess.check_output', side_effect=raise_exception_twice)
    KrbCommand.kinit(config)
    assert patcher.call_count == 3


def test_no_retry_when_filenotfound(config, mocker):
    KrbCommand.kdestroy(config)

    raise_exception = [
        FileNotFoundError,
        None]
    patcher = mocker.patch('subprocess.check_output', side_effect=raise_exception)
    try:
        KrbCommand.kinit(config)
        pytest.fail()
    except FileNotFoundError:
        assert patcher.call_count == 1


@pytest.mark.parametrize('config,expected', [
    (KrbConfig(
        principal=DEFAULT_PRINCIPAL,
        keytab=DEFAULT_KEYTAB,
        ticket_lifetime=DEFAULT_TICKET_LIFETIME,
        ticket_renewable_lifetime=DEFAULT_TICKET_RENEWABLE_LIFETIME),
    ['kinit', '-l', DEFAULT_TICKET_LIFETIME, '-r', DEFAULT_TICKET_RENEWABLE_LIFETIME, '-c', DEFAULT_CCACHE_NAME, '-k', '-t', './tests/conf/krb5.keytab', 'user@EXAMPLE.COM']),
    (KrbConfig(
        principal='alice@EXAMPLE.COM',
        keytab=DEFAULT_KEYTAB,
        ticket_lifetime=DEFAULT_TICKET_LIFETIME,
        ticket_renewable_lifetime=DEFAULT_TICKET_RENEWABLE_LIFETIME),
    ['kinit', '-l', DEFAULT_TICKET_LIFETIME, '-r', DEFAULT_TICKET_RENEWABLE_LIFETIME, '-c', DEFAULT_CCACHE_NAME, '-k', '-t', './tests/conf/krb5.keytab', 'alice@EXAMPLE.COM']),
    (KrbConfig(
        principal=DEFAULT_PRINCIPAL,
        keytab=None,
        ticket_lifetime='1s',
        ticket_renewable_lifetime=DEFAULT_TICKET_RENEWABLE_LIFETIME),
    ['kinit', '-l', '1s', '-r', DEFAULT_TICKET_RENEWABLE_LIFETIME, '-c', DEFAULT_CCACHE_NAME, '-k', 'user@EXAMPLE.COM']),
    (KrbConfig(
        principal=DEFAULT_PRINCIPAL,
        keytab=DEFAULT_KEYTAB,
        ticket_lifetime=DEFAULT_TICKET_LIFETIME,
        ticket_renewable_lifetime='6s'),
    ['kinit', '-l', DEFAULT_TICKET_LIFETIME, '-r', '6s', '-c', DEFAULT_CCACHE_NAME, '-k', '-t', './tests/conf/krb5.keytab', 'user@EXAMPLE.COM']),
    ])
def test_kinit_command(config, expected, mocker):
    mocker.patch.object(KrbCommand, '_call')
    KrbCommand.kinit(config)
    KrbCommand._call.assert_called_with(config, expected)
