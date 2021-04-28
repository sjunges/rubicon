import subprocess
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Storm:
    def __init__(self, cwd, path, arguments, symbolic):
        self._path = path.split(" ")
        self._cwd = cwd
        self._id = "storm" + ("-dd" if symbolic else "-sparse")
        if len(arguments) > 0:
            self._id += "-" + "-".join(arguments)
        if arguments is None:
            self._arguments = ['-tm', '--sylvan:threads', '1']
        else:
            self._arguments = arguments + ['-tm', '--sylvan:threads', '1']
        if symbolic:
            self._arguments += ['-e', 'dd']

    @property
    def id(self):
        return self._id

    def run(self, prism_path, prop, constants):
        invocation = self._path + ["--prism", prism_path, "--prop", prop, "-const", constants] + self._arguments
        stats = dict()

        stats["file"] = prism_path
        try:
            logger.info("Run Storm... " + " ".join(invocation) + " from " + self._cwd)
            stdout = subprocess.check_output(invocation, timeout=1000, cwd=self._cwd)
            # stdout, stderr = process.communicate()
            stdout = stdout.decode("utf-8")
            for line in stdout.split("\n"):
                if line.startswith("Result"):
                    stats["result"] = line.split(":")[1].strip()
                if line.strip().startswith("* wallclock"):
                    stats["total_time"] = line.split(":")[1].strip()[:-1]

            logger.info(f"Done: Result: {stats['result']}. Took {stats['total_time']}s")
            return stats
        except subprocess.TimeoutExpired:
            stats["total_time"] = -1
            stats["result"] = -1
            logger.info(f"Done: Result: {stats['result']}. Took {stats['total_time']}s")
            return stats



