import subprocess
import logging
import json


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Dice:
    def __init__(self, cwd, path, arguments, timeout):
        self._path = path.split(" ")
        self._cwd = cwd
        self._timeout = timeout
        if arguments is None:
            self._arguments = ["-json", "-time"]
        else:
            self._arguments = arguments + ["-json", "-time"]


    def run(self, file):
        invocation = self._path + self._arguments + [file]
        logger.info("Run Dice... " + " ".join(invocation) + " from " + self._cwd)
        stats = dict()
        stats["file"] = file
        try:
            stdout = subprocess.check_output(invocation, timeout=self._timeout, cwd=self._cwd)
            stdout = stdout.decode("utf-8")
            # stderr = stderr.decode("utf-8")
            # logger.debug(stdout)
            # logger.debug(stderr)
            j = json.loads(stdout)
            stats["total_time"] = j[1]["Total time"]
            stats["result"] = str(j[0]["Joint Distribution"][2][1])
            #
            logger.info(f"Done: Result: {stats['result']}. Took {stats['total_time']}s")
            return stats
        except subprocess.TimeoutExpired:
            stats["total_time"] = -1
            stats["result"] = -1
            logger.info(f"Time out")
            return stats
        except subprocess.CalledProcessError:
            stats["total_time"] = -1
            stats["result"] = -1
            logger.info(f"Process Error")
            return stats
