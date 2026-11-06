from pathlib import Path

BASE_URL = "https://bulbapedia.bulbagarden.net/w/api.php"
LIST_PAGE = "List of Pokémon by National Pokédex number"

USER_AGENT = "GottaCatchEmAll-Project4/0.1"
REQUEST_DELAY_SECONDS = 1.0

DATA_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = DATA_DIR/"cache"
RAW_DIR = DATA_DIR/"raw"
FAILURES_LOG = DATA_DIR/"failures.log"

DEFAULT_MAX_DEX = 151 # placeholder, gen 1 for now
GEN_END = [
    (1, 151),
    (2, 251),
    (3, 386),
    (4, 493),
    (5, 649),
    (6, 721),
    (7, 809),
    (8, 905),
    (9, 1025),
]

SKIP_SECTIONS = {
    "see also", 
    "external links", 
    "references", 
    "notes", 
    "sprites", 
    "gallery",
    "in other languages", 
    "related articles",
    "in animation", 
    "in the manga", 
    "in the tcg", 
    "in the tfg",
    "other appearances", 
    "merchandise",
}