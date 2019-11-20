import os
import subprocess
import logging
from retrying import retry


class KrbCommand():
    @staticmethod
    def kinit(config):
        commands = []
        commands.append(config.kinit_bin)
        if config.ticket_lifetime:
            commands.append("-l")
            commands.append(config.ticket_lifetime)
        commands.append("-k")
        commands.append("-t")
        commands.append(config.keytab)
        commands.append(config.principal)

        KrbCommand._call(config, commands)

    @staticmethod
    def renewal(config):
        commands = []
        commands.append(config.kinit_bin)
        commands.append("-k")
        commands.append("-t")
        commands.append(config.keytab)
        commands.append("-R")
        commands.append(config.principal)

        KrbCommand._call(config, commands)

    @staticmethod
    def klist(config):
        commands = []
        commands.append(config.klist_bin)
        return KrbCommand._call(config, commands)

    @staticmethod
    def kdestroy(config):
        commands = []
        commands.append(config.kdestroy_bin)
        return KrbCommand._call(config, commands)

    @staticmethod
    def _call(config, commands):

        @retry(**config.retry_options)
        def retriable_call():
            logging.debug("Executing {}".format(" ".join(commands)))
            custom_env = os.environ.copy()
            custom_env["LC_ALL"] = "C"
            return subprocess.check_output(commands, universal_newlines=True, env=custom_env)

        return retriable_call()
