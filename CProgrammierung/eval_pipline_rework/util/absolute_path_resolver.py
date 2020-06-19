import sys
from pathlib import Path


def resolve_absolute_path(s):
    file_name = sys.argv[0]
    file_name = file_name.replace("__main__.py", "").replace(".", "")
    config_path = Path(file_name + s).resolve()
    return config_path
