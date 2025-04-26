from src.fetch_old import Fetcher as Fold
from src.fetch import Fetcher
from src.trans import *
from src.replacer import *
from src.HTMLUpdate import *
import sys

def update(oldversion, newversion):
    fetch = Fetcher(newversion) # new version
    fetch2 = Fetcher(oldversion) # old version
    fetch.marge_source()
    # fetch.convert_to_pz()
    # fetch.hash_update()
    # fetch.position_update()
    fetch2.compare_source(newversion) # compare with new version
    # fetch.fetch_source()
    fetch.convert_to_pz()
    # fetch2.fetch_source()
    # fetch2.convert_to_pz()
    # fetch.pz_token_update()

oldversion, newversion = sys.argv[1], sys.argv[2]
update(oldversion, newversion)