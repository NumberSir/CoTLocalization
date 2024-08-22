from src.fetch_old import Fetcher as Fold
from src.fetch import Fetcher
from src.trans import *
from src.replacer import *
from src.HTMLUpdate import *

def main():
    # fetch = Fetcher()
    # fetch.fetch_source()
    # fetch.convert_to_pz()
    # fetch.pz_token_update()
    # replace = Replacer()
    # replace.replace_file()
    # oldfetch = Fold()
    # oldfetch.fetch_source()
    # oldfetch.convert_to_pz()
    # trans()

    updater = HTMLUpdater("CourseOfTemptation.html")
    updater.update_main("CoT.html")

if __name__ == '__main__':
    main()