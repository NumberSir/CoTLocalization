from src.fetch_old import Fetcher as Fold
from src.fetch import Fetcher
from src.trans import *
from src.replacer import *
from src.HTMLUpdate import *

def main():
    fetch = Fetcher("yohi") # new version
    fetch2 = Fetcher("yohiori") # old version
    # fetch.marge_source()
    # fetch.convert_to_pz()
    # fetch.hash_update()
    # fetch.position_update()
    # fetch2.compare_source('yohi') # compare with new version
    # fetch.fetch_source()
    fetch.convert_to_pz()
    # fetch2.fetch_source()
    # fetch2.convert_to_pz()
    # fetch.pz_token_update()

if __name__ == '__main__':
    main()