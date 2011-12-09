from googlenews import GoogleNews
from alchemyapi import AlchemyAPI
from wikicategories import CategoryScraper
from pymongo import Connection
import logging
logging.basicConfig(level=logging.DEBUG)
from gensimtools import GensimSearcher
import re
import collections

def get_connection():
    return Connection()['localangle']

def update_all():
    update_stories()
    update_entities()
    update_contexts()

def update_stories():
    db = get_connection()
    gn = GoogleNews()
    
    original_count = db.stories.count()
    for topic in ['h', 'w', 'b', 'n', 't', 'el', 'p', 'e', 's', 'm']:
        for story in gn.from_topic(topic):
            if not db.stories.find_one({ 'unescapedUrl' : story['unescapedUrl'] }):
                db.stories.insert(story)
    logging.debug('Added %s new stories', db.stories.count() - original_count)
        
def update_entities():
    db = get_connection()
    alchemy = AlchemyAPI()
    
    for story in db.stories.find({ 'entities' : { '$exists' : False }}):
        entities = alchemy.analyze_url(story['unescapedUrl'])['entities']
        logging.debug('%s, %s entities' % (story['title'], len(entities)))
        story['entities'] = entities
        db.stories.save(story)

def debug():
    COSINE_THRESHOLD = .75
    searcher = GensimSearcher('companies_index')
    db = get_connection()
    company_name_difference = collections.defaultdict(int)
    for story in db.stories.find({ 'entities' : { '$exists' : True }}):
        for entity in story['entities']:
            
            if entity['type'] == 'Organization' and 'disambiguated' in entity and 'subType' in entity['disambiguated'] and 'CollegeUniversity' in entity['disambiguated']['subType']:
                print entity['text'] + ' - ' + entity['disambiguated']['name']
            
            """
            if entity['type'] == 'Company':
                search_results = searcher.search(entity['text'])
                if any(search_results) and search_results[0][1] > COSINE_THRESHOLD:
                    company = db.companies.find_one({ 'name' : search_results[0][0] })
                    for location in company['location']:
                        
                        if entity['text'].lower() != company['name'].lower():
                            print location
                            print entity['text']
                            print company['name']
                            print compare_companies(entity['text'], company['name'])
                            print set(entity['text'].lower().split()) - set(company['name'].lower().split())
                            for diff in set(entity['text'].lower().split()) - set(company['name'].lower().split()):
                                company_name_difference[diff] += 1
                        print
            """
    return company_name_difference

def remove_punctuation(text):
    return re.sub('[^a-z|\d|\s]', '', text)

def compare_companies(company1, company2):
    company1 = remove_punctuation(company1.lower())
    company2 = remove_punctuation(company2.lower())

    stop_list = ['inc', 'corp', 'co', 'group', 'ltd', 'company', 'amp', 'entertainment', 'communcations', 'systems']
    company1 = ' '.join(filter(lambda word: word not in stop_list, company1.split()))
    company2 = ' '.join(filter(lambda word: word not in stop_list, company2.split()))

    return company1 == company2

def update_contexts(incremental=True):
    COSINE_THRESHOLD = .75
    db = get_connection()
    
    company_criteria = { 'entities' : { '$exists' : True } }
    if incremental:
        company_criteria['contexts'] = { '$exists' : False }
    
    for story in db.stories.find(company_criteria):
        
        story['contexts'] = []
        
        for entity in story['entities']:
            if entity['type'] == 'Company':
                
                for company in db.companies.find():
                    if compare_companies(entity['text'], company['name']):
                        for location in company['location']:
                            logging.debug('%s, %s, %s' % (story['title'], location, entity['text']))
                            story['contexts'].append({
                                    'location' : location,
                                    'name' : entity['text'],
                                    'type' : entity['type']
                                    })
                        break
                        
        db.stories.save(story)
               
def distinct_companies():
    db = get_connection()
    companies = []
    for story in db.stories.find({ 'entities' : { '$exists' : True }}):
        for entity in story['entities']:
            if entity['type'] == 'Company':
                companies.append(entity['text'].lower())
    return sorted(list(set(companies)))