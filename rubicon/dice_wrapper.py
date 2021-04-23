import subprocess
import logging

logger = logging.getLogger(__name__)


class Dice:
    def __init__(self, cwd, path, arguments):
        self._path = path.split(" ")
        self._cwd = cwd
        if arguments is None:
            self._arguments = []
        else:
            self._arguments = arguments

    def run(self, file):
        logger.info("Run Dice...")
        process = subprocess.Popen(self._path + self._arguments + [file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self._cwd)
        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")
        print(stdout)
        print(stderr)
        logger.info("Done. ")



