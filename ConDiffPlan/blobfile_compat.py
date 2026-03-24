"""
Minimal blobfile compatibility layer for local filesystem paths.

This keeps training and checkpoint code working when the optional
`blobfile` dependency is not installed.
"""

import os


class BlobFile:
    def __init__(self, path, mode="rb", *args, **kwargs):
        if any(path.startswith(prefix) for prefix in ("gs://", "s3://", "az://")):
            raise ImportError(
                "blobfile is required for non-local storage paths. "
                "Install it with `pip install blobfile`."
            )

        self.path = path
        self.mode = mode
        self.args = args
        self.kwargs = kwargs
        self._fh = None

    def __enter__(self):
        if any(flag in self.mode for flag in ("w", "a", "x", "+")):
            parent = os.path.dirname(self.path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        self._fh = open(self.path, self.mode, *self.args, **self.kwargs)
        return self._fh

    def __exit__(self, exc_type, exc, tb):
        if self._fh is not None:
            self._fh.close()
        return False


def join(*parts):
    return os.path.join(*parts)


def dirname(path):
    return os.path.dirname(path)


def exists(path):
    return os.path.exists(path)
