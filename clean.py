
from src.fetch import Fetcher
import sys

def clean(v):
    fetch = Fetcher(v) # new version
    fetch.clean_obsolete_entries()

v = sys.argv[1]
clean(v)