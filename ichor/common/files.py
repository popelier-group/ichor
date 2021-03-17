import shutil
from pathlib import Path

# from functools import wraps
# from itertools import zip_longest


# TODO: Think how to convert path arguments to Path instance
# def convert_to_path(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         if func.__annotations__:
#             annotations = func.__annotations__.items()
#             for i, ((annotation, type_), arg) in enumerate(zip_longest(annotations, args)):
#                 if annotation and arg:
#                     if type_ is Path:
#                         args[i] = Path(arg)


# @convert_to_path
def mkdir(path: Path, empty: bool = False, force: bool = True):
    if path.is_dir() and empty:
        try:
            shutil.rmtree(directory)
        except OSError as err:
            if force:
                print(str(err))
                sys.exit(1)
    os.makedirs(directory, exist_ok=True)
