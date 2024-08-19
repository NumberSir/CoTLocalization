from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

DIR_ROOT = Path(__file__).parent.parent
DIR_SOURCE = DIR_ROOT/"source"
DIR_MARGE_SOURCE = DIR_ROOT/"marge_source"
DIR_FETCH = DIR_ROOT/"fetch"
DIR_PZ_ORIGIN = DIR_ROOT/"pz_origin"