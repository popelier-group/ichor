""" Import tqdm or dummy_tqdm if tqdm is not present. dummy_tqdm does nothing but it needs to be loaded on compute nodes instead of tqdm because tqdm messes up
the formatting of output/error files. If GLOBALS.SUBMITTED is True (so job is submitted to compute node), then load up dummy tqdm."""

from .common.types.dummy_tqdm import dummy_tqdm
from .globals import GLOBALS

try:
    from tqdm import tqdm
except:
    tqdm = dummy_tqdm

if GLOBALS.SUBMITTED:
    tqdm = dummy_tqdm
