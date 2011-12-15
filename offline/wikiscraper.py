from wikicategories import CategoryScraper
from pymongo import Connection
import re
import logging
logging.basicConfig(level=logging.DEBUG)

def get_connection():
    return Connection()['localangle']
    
def scrape_and_store_all_universities():
    db = get_connection()
    url = 'http://en.wikipedia.org/wiki/Category:Universities_and_colleges_in_the_United_States_by_state'
    #url = 'http://en.wikipedia.org/wiki/Category:Universities_and_colleges_in_the_United_States_by_city'
    scrape_and_store_subcategories(url, 'Universities and colleges (of|in) (?P<location>.*)', db.universities)

def scrape_and_store_companies_by_city():
    db = get_connection()
    scrape_and_store_subcategories('http://en.wikipedia.org/wiki/Category:Companies_by_city_in_the_United_States', 'Companies based in (?P<location>.*)', db.companies)

def scrape_and_store_companies_by_state():
    db = get_connection()
    scrape_and_store_subcategories('http://en.wikipedia.org/wiki/Category:Companies_of_the_United_States_by_state', 'Companies based (of|in) (?P<location>.*)', db.companies)
    
#################################################

def scrape_and_store_subcategories(url, location_regex, db_collection):
    wiki = CategoryScraper()
    for text, url in wiki.scrape_subcategories(url):
        location_pattern = re.compile(location_regex, flags=re.IGNORECASE)
        location_search = location_pattern.search(text)
        if location_search:
            logging.debug(text)
            location = location_search.group('location')
            scrape_and_store_subcategories(url, location_regex, db_collection)
            scrape_and_store_pages(url, location, db_collection)
        
def scrape_and_store_pages(url, location, db_collection):
    wiki = CategoryScraper()
    pages = wiki.scrape_pages(url)
    logging.debug('%s, %s pages' % (location, len(pages)))        
    for page in pages:
        db_collection.update({ 'name' : page.lower() }, { '$addToSet' : { 'locations' : parse_location(location) }}, upsert=True)
        
def parse_location(location):
    if len(location.split(',')) > 1:
        city = location.split(',')[0].strip()
        state = location.split(',')[1].strip()
    else:
        city = None
        state = location.strip()
        
    return {
        'city' : city,
        'state' : state
    }
    