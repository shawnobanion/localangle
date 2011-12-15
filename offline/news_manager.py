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
    cleaned_company_names = collections.defaultdict(str, [(clean_company_name(company['name']), company['name']) for company in db.companies.find()])
    
    story_criteria = { 'entities' : { '$exists' : True } }
    if incremental:
        story_criteria['contexts'] = { '$exists' : False }
    
    for story in db.stories.find(story_criteria):
        
        story['contexts'] = []
        
        for entity in story['entities']:
            if entity['type'] == 'Company':
                
                cleaned_entity_name = clean_company_name(entity['text'])
                lookup_company_name = cleaned_company_names[cleaned_entity_name]
                                
                if lookup_company_name:
                    company = db.companies.find_one( { 'name' : lookup_company_name })
                                        
                    for location in company['locations']:
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
        db.stories.save(story)
               
def update_headlines_blurbs(incremental=True):
    db = get_connection()

    alchemy = AlchemyAPI()
    

    story_criteria = { 'entities' : { '$exists' : True }, 'contexts' : { '$exists' : True, '$ne' : [] }}
    if incremental:
        story_criteria['contexts.headline'] = { '$exists' : False }
            
    for story in db.stories.find(story_criteria):
        for context in story['contexts']:
            context['headline'] = None
            display_location = context['location']['city'] if context['location']['city'] else context['location']['state']
            for entity in context['entities']:
                new_headline = rewrite_with_entity_location(story['titleNoFormatting'], entity['name'], display_location)
                if new_headline:
                    logging.debug(new_headline)
                    context['headline'] = new_headline
                for i, instance in enumerate(entity['instances']):
                    entity['instances'][i] = rewrite_with_entity_location(instance, alchemy._escape_special_chars(entity['name']), display_location, clean_entity_name=False)
                    assert(entity['instances'][i])
        db.stories.save(story)
        
def rewrite_with_entity_location(text, entity, display_location, clean_entity_name=True):
    entity_pattern = re.compile('\\b(?P<entity>%s)\\b' % (clean_company_name(entity, robust=True) if clean_entity_name else entity), flags=re.IGNORECASE)
    entity_search = entity_pattern.search(text)
    if entity_search:
        return entity_pattern.sub('<span class=\"context\">%s-based %s</span>' % (display_location, entity_search.group('entity')), text)
    return None