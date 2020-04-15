import fasteners
import logging
import os
import subprocess
import threading
from retrying import retry

logger = logging.getLogger(__name__)
# fasteners is for interprocess multiprocessing
# threading.Lock is for multithreading
lock = threading.Lock()


class KrbCommand():
    @staticmethod
    def kinit(config):
        commands = []
        commands.append(config.kinit_bin)
        if config.ticket_lifetime:
            commands.append("-l")
            commands.append(config.ticket_lifetime)
        if config.ticket_renewable_lifetime:
            commands.append("-r")
            commands.append(config.ticket_renewable_lifetime)
        if config.ccache_name:
            commands.append("-c")
            commands.append(config.ccache_name)
        commands.append("-k")
        if config.keytab:
            commands.append("-t")
            commands.append(config.keytab)
        commands.append(config.principal)

        KrbCommand._call(config, commands)

    @staticmethod
    def renewal(config):
        commands = []
        commands.append(config.kinit_bin)
        if config.ccache_name:
            commands.append("-c")
            commands.append(config.ccache_name)
        commands.append("-R")
        commands.append(config.principal)

        KrbCommand._call(config, commands)

    @staticmethod
    def klist(config):
        commands = []
        commands.append(config.klist_bin)
        if config.ccache_name:
            commands.append("-c")
            commands.append(config.ccache_name)
        return KrbCommand._call(config, commands)

    @staticmethod
    def kdestroy(config):
        commands = []
        commands.append(config.kdestroy_bin)
        if config.ccache_name:
            commands.append("-c")
            commands.append(config.ccache_name)
        return KrbCommand._call(config, commands)

    @staticmethod
    def cache_exists(config):
        with lock:
            with fasteners.InterProcessLock(config.ccache_cmd_lockfile):
                return os.path.isfile(config.ccache_name)

    @staticmethod
    def _call(config, commands):

        def error_on_retry(exception):
            # will not retry if command is not found.
            if type(exception) == FileNotFoundError:
                raise exception

            logger.warning("the command failed. attempting retry... retry_options={}".format(config.retry_options))
            return True

        retry_options = {**config.retry_options, **{'retry_on_exception': error_on_retry}}
        @retry(**retry_options)
        def retriable_call():
            logger.debug("Executing {}".format(" ".join(commands)))
            custom_env = os.environ.copy()
            custom_env["LC_ALL"] = "C"
            return subprocess.check_output(commands, universal_newlines=True, env=custom_env)

        with lock:
            with fasteners.InterProcessLock(config.ccache_cmd_lockfile):
                return retriable_call()
