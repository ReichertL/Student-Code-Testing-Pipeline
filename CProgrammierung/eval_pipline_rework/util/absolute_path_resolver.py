import os
import sys
from pathlib import Path


def resolve_absolute_path(s):
    file_name = os.path.realpath(sys.argv[0])
    file_name = file_name.replace("__main__.py", "").replace(".", "").replace("checkpy", "")
    if not len(file_name) > 0:
        if s[0] == os.path.sep:
            return s[1:]
        return s
    if file_name[-1] != os.path.sep and s[0] != os.path.sep:
        file_name = file_name + os.path.sep
    file_name = file_name + s
    config_path = Path(file_name).resolve()
    return config_path
