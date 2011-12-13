from gensimtools import GensimSearcher, GensimIndexer
from pymongo import Connection
import collections

def get_connection():
    return Connection()['localangle']
    
def index_companies():
    db = get_connection()
    indexer = GensimIndexer('companies_index')
    indexer.index(db.companies.distinct('name'))
    
def debug():
    COSINE_THRESHOLD = .75
    searcher = GensimSearcher('companies_index')
    db = get_connection()
    company_name_difference = collections.defaultdict(int)
    for story in db.stories.find({ 'entities' : { '$exists' : True }}):
        for entity in story['entities']:           
            
            if entity['type'] == 'Company':
                
                search_results = searcher.search(entity['text'])
                if any(search_results) and search_results[0][1] > COSINE_THRESHOLD:
                
                    company = db.companies.find_one({ 'name' : search_results[0][0] })
                
                    if entity['text'].lower() != company['name'].lower():
                        print entity['text']
                        print company['name']
                        print set(entity['text'].lower().split()) ^ set(company['name'].lower().split())
                        for diff in set(entity['text'].lower().split()) ^ set(company['name'].lower().split()):
                            company_name_difference[diff] += 1
                        print
            
    return company_name_difference

def foo():
    db = get_connection()
    searcher = GensimSearcher('companies_index')
    COSINE_THRESHOLD = .75
    
    all_companies = set([entity['text'] for story in db.stories.find() for entity in story['entities'] if entity['type'] == 'Company'])
    matched_companies = set(db.stories.distinct('contexts.entities.name'))
        
    for company in all_companies - matched_companies:
        search_results = searcher.search(company)[:1]
        if any(search_results) and search_results[0][1] > COSINE_THRESHOLD:
            print company
            print search_results[0][0]
            print