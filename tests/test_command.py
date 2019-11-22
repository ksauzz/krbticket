from krbticket import KrbConfig, KrbCommand
from helper import *
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


def test_multiprocess_ccache(config):
    KrbCommand.kdestroy(config)

    def run():
        conf = default_config()
        assert conf.ccache_name.startswith(config.ccache_name)
        assert conf.ccache_name != config.ccache_name
        _test_commands(conf)

    processes = [Process(target=run) for i in range(5)]
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
        fail()
    except FileNotFoundError:
        assert patcher.call_count == 1

