from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

VERSION = '0.5.2f'
VERSION2 = '0.5.3c'

DIR_ROOT = Path(__file__).parent.parent
DIR_SOURCE = DIR_ROOT/"source"
DIR_OLD_SOURCE = DIR_ROOT/"oldsource"
DIR_MARGE_SOURCE = DIR_ROOT/"marge_source"
DIR_FETCH = DIR_ROOT/"fetch"
DIR_OLD_FETCH = DIR_ROOT/"oldfetch"
DIR_PZ_ORIGIN = DIR_ROOT/"pz_origin"

DIR_TRANS = DIR_ROOT/"trans"
DIR_TRANSLATED_SOURCE = DIR_ROOT/"translated_source"