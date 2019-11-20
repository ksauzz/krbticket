from krbticket import KrbConfig, KrbCommand
from helper import config


def test_commands(config):
    KrbCommand.kdestroy(config)
    KrbCommand.kinit(config)
    KrbCommand.renewal(config)
    KrbCommand.klist(config)
