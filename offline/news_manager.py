from googlenews import GoogleNews
from alchemyapi import AlchemyAPI
from wikicategories import CategoryScraper
from pymongo import Connection, objectid
import logging
logging.basicConfig(level=logging.DEBUG)
import re
import collections
from utils import clean_company_name, remove_punctuation

def get_connection():
    return Connection()['localangle']

def update_all():
    update_stories()
    update_entities()
    update_contexts()
    update_headlines_blurbs()

def update_stories():
    db = get_connection()
    gn = GoogleNews()
    
    original_count = db.stories.count()
    for topic in ['h', 'w', 'b', 'n', 't', 'el', 'p', 'e', 's', 'm']:
        for story in gn.from_topic(topic):
            if not db.stories.find_one({ 'unescapedUrl' : story['unescapedUrl'] }):
                db.stories.insert(story)
    logging.debug('Added %s new stories', db.stories.count() - original_count)
        
def update_entities(incremental=True):
    db = get_connection()
    alchemy = AlchemyAPI()
    
    story_criteria = {}
    if incremental:
        story_criteria = { 'entities' : { '$exists' : False } }
        
    for story in db.stories.find(story_criteria):
        entities = alchemy.analyze_url(story['unescapedUrl'])['entities']
        logging.debug('%s, %s entities' % (story['title'], len(entities)))
        story['entities'] = entities
        db.stories.save(story)

def update_contexts(incremental=True):
    COSINE_THRESHOLD = .75
    db = get_connection()
    
    # Cache the cleaned company names
    cleaned_company_names = dict([(company['name'], clean_company_name(company['name'])) for company in db.companies.find()])
    
    story_criteria = { 'entities' : { '$exists' : True } }
    if incremental:
        story_criteria['contexts'] = { '$exists' : False }
    
    for story in db.stories.find(story_criteria):
        
        story['contexts'] = []
        
        for entity in story['entities']:
            if entity['type'] == 'Company':
                
                cleaned_entity_name = clean_company_name(entity['text'])
                
                for company in db.companies.find():
                    if cleaned_entity_name == cleaned_company_names[company['name']]:
                        
                        for location in company['location']:
                            logging.debug('%s, %s, %s' % (story['title'], location, entity['text']))
                            
                            # Check to see if the location already exists in the contexts                            
                            location_exists = any([context for context in story['contexts'] if context['location'] == location])
                            if not location_exists:
                                story['contexts'].append({
                                    'location' : location,
                                    'entities' : [{
                                        'name' : entity['text'],
                                        'type' : entity['type'],
                                        'instances' : entity['instances']
                                    }]
                                })
                            else:
                                for context in story['contexts']:
                                    if context['location'] == location:
                                        context['entities'].append({
                                            'name' : entity['text'],
                                            'type' : entity['type'],
                                            'instances' : entity['instances']
                                        })        
                            
                        break

        db.stories.save(story)
               
def update_headlines_blurbs():
    db = get_connection()
    for story in db.stories.find({ 'entities' : { '$exists' : True }, 'contexts' : { '$exists' : True }}):
        for context in story['contexts']:
            for entity in context['entities']:
                
                # If the entity exists in the story headline, rewrite it
                entity_pattern = re.compile('\\b(?P<entity>%s)\\b' % clean_company_name(entity['name'], robust=True), flags=re.IGNORECASE)
                entity_search = entity_pattern.search(story['titleNoFormatting'])
                if entity_search:
                    display_location = context['location'].split(',')[0] if len(context['location'].split(',')) > 1 else context['location']
                    new_headline = entity_pattern.sub('%s-based %s' % (display_location, entity_search.group('entity')), story['titleNoFormatting'])
                    logging.debug(new_headline)
                    context['headline'] = new_headline
                    break
                
        db.stories.save(story)               