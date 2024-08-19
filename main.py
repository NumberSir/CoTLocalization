from src.fetch import *

def main():
    fetch = Fetcher()
    # fetch.marge_source()
    fetch.fetch_source()
    fetch.convert_to_pz()

if __name__ == '__main__':
    main()