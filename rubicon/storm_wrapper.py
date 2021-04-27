class Storm:
    def __init__(self, cwd, path, arguments):
        self._path = path.split(" ")
        self._cwd = cwd
        if arguments is None:
            self._arguments = []
        else:
            self._arguments = arguments + []

    def run(self):
        return dict()