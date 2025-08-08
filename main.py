from src.fetch_old import Fetcher as Fold
from src.fetch import Fetcher
from src.trans import *
from src.replacer import *
from src.HTMLUpdate import *
import sys

def main(version):
    fetch = Fetcher(version)
    # fetch2 = Fetcher("0.5.5b")
    fetch.marge_source()
    # fetch.convert_to_pz()
    # fetch.hash_update()
    # fetch.position_update()
    # fetch2.compare_source('0.5.5c')
    fetch.fetch_source()
    fetch.convert_to_pz()
    # fetch2.fetch_source()
    # fetch2.convert_to_pz()
    # fetch.pz_token_update()
    replace = Replacer(version)
    # replace.replace_file()
    replace.convert_to_i18n()
    # oldfetch = Fold()
    # oldfetch.fetch_source()
    # oldfetch.convert_to_pz()
    # trans("0.5.4d-new", "0.5.4d-translated")
    # trans_from_pz("0.5.3c-new","0.5.3c-new2")

main(sys.argv[1])
if (len(sys.argv)>2 and sys.argv[2]=="file"):
    replace = Replacer(sys.argv[1])
    replace.replace_file()