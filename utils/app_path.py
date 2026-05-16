import os
import sys


def _is_frozen():
    return getattr(sys, 'frozen', False)


def get_data_path(filename: str) -> str:
    if _is_frozen():
        from platformdirs import user_data_dir
        data_dir = user_data_dir("PsCafeManagement")
        os.makedirs(data_dir, exist_ok=True)
    else:
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.normpath(os.path.join(data_dir, filename))


def get_resource_path(relative_path: str) -> str:
    if _is_frozen():
        return os.path.normpath(os.path.join(sys._MEIPASS, relative_path))
    return os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path))
