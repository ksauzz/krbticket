from krbticket import KrbConfig, KrbCommand
from helper import config
import subprocess


def test_commands(config):
    KrbCommand.kdestroy(config)
    KrbCommand.kinit(config)
    KrbCommand.renewal(config)
    KrbCommand.klist(config)


def test_retry_command(config, mocker):
    KrbCommand.kdestroy(config)

    raise_exception_twice = [
        subprocess.CalledProcessError(1, ['kinit']),
        subprocess.CalledProcessError(1, ['kinit']),
        None]
    patcher = mocker.patch('subprocess.check_output', side_effect=raise_exception_twice)
    KrbCommand.kinit(config)
    assert patcher.call_count == 3
