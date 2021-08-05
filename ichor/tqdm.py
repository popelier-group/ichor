from .common.types.dummy_tqdm import dummy_tqdm
from .globals import GLOBALS

try:
    from tqdm import tqdm
except:
    tqdm = dummy_tqdm

if GLOBALS.SUBMITTED:
    tqdm = dummy_tqdm
