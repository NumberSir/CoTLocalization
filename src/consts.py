from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

VERSION = '0.5.2d'

DIR_ROOT = Path(__file__).parent.parent
DIR_SOURCE = DIR_ROOT/"source"/VERSION
DIR_OLD_SOURCE = DIR_ROOT/"oldsource"/VERSION
DIR_MARGE_SOURCE = DIR_ROOT/"marge_source"/VERSION
DIR_FETCH = DIR_ROOT/"fetch"/VERSION
DIR_OLD_FETCH = DIR_ROOT/"oldfetch"/VERSION
DIR_PZ_ORIGIN = DIR_ROOT/"pz_origin"/VERSION

DIR_TRANS = DIR_ROOT/"trans"/VERSION
DIR_TRANSLATED_SOURCE = DIR_ROOT/"translated_source"/VERSION