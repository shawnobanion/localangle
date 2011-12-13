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
    scrape_and_store_subcategories('http://en.wikipedia.org/wiki/Category:Companies_of_the_United_States_by_state', 'Companies based in (?P<location>.*)', db.companies)
    
#################################################

def scrape_and_store_subcategories(url, location_regex, db_collection):
    wiki = CategoryScraper()
    for text, url in wiki.scrape_subcategories(url):
        location = re.search(location_regex, text).group('location')
        scrape_and_store_pages(url, location, db_collection)
        
def scrape_and_store_pages(url, location, db_collection):
    wiki = CategoryScraper()
    pages = wiki.scrape_pages(url)
    logging.debug('%s, %s pages' % (location, len(pages)))
    for page in pages:
        db_collection.update({ 'name' : page.lower() }, { '$addToSet' : { 'location' : location }}, upsert=True)