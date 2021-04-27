import subprocess
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Storm:
    def __init__(self, cwd, path, arguments, symbolic):
        self._path = path.split(" ")
        self._cwd = cwd
        if arguments is None:
            self._arguments = ['-tm', '--sylvan:threads', '1']
        else:
            self._arguments = arguments + ['-tm', '--sylvan:threads', '1']
        if symbolic:
            self._arguments += ['-e', 'dd']

    def run(self, prism_path, prop, constants):
        stats = dict()
        stats["file"] = prism_path
        process = subprocess.Popen(self._path + ["--prism", prism_path, "--prop", prop, "-const", constants] + self._arguments, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, cwd=self._cwd)
        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")
        for line in stdout.split("\n"):
            if line.startswith("Result"):
                stats["result"] = line.split(":")[1].strip()
            if line.strip().startswith("* wallclock"):
                stats["total_time"] = line.split(":")[1].strip()[:-1]

        logger.info(f"Done: Result: {stats['result']}. Took {stats['total_time']}s")
        return stats