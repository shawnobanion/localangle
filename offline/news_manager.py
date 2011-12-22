from googlenews import GoogleNews
from alchemyapi import AlchemyAPI
from wikicategories import CategoryScraper
from pymongo import Connection, objectid
import logging
logging.basicConfig(level=logging.DEBUG)
import re
import collections
from utils import clean_company_name, remove_punctuation
import itertools

_db = Connection()['localangle']

def update_all():
    update_stories()
    update_entities()
    update_contexts()
    transform_headlines_blurbs()

def update_stories():
    gn = GoogleNews()
    
    original_count = _db.stories.count()
    for topic in ['h', 'w', 'b', 'n', 't', 'el', 'p', 'e', 's', 'm']:
        for story in gn.from_topic(topic):
            if not _db.stories.find_one({ 'unescapedUrl' : story['unescapedUrl'] }):
                _db.stories.insert(story)
    logging.debug('Added %s new stories', _db.stories.count() - original_count)
        
def update_entities(incremental=True):
    alchemy = AlchemyAPI()
    
    story_criteria = {}
    if incremental:
        story_criteria = { 'entities' : { '$exists' : False } }
        
    for story in _db.stories.find(story_criteria):
        entities = alchemy.analyze_url(story['unescapedUrl'])['entities']
        logging.debug('%s, %s entities' % (story['title'], len(entities)))
        story['entities'] = entities
        _db.stories.save(story)

def find_company_contexts(alchemyapi_entity, localangle_company_names):
    return find_contexts(alchemyapi_entity, 'Company', clean_company_name, localangle_company_names, _db.companies)

def find_person_contexts(alchemyapi_entity, localangle_person_names):
    return find_contexts(alchemyapi_entity, 'Person', lambda name: name.lower(), localangle_person_names, _db.persons)
                
def find_contexts(alchemyapi_entity, alchemyapi_entity_type, alchemyapi_entity_name_fn, localangle_entity_names, localangle_entity_db_col):
    
    if alchemyapi_entity['type'] == alchemyapi_entity_type:
        localangle_entity_name = localangle_entity_names.get(alchemyapi_entity_name_fn(alchemyapi_entity['text']), None)
       
        if localangle_entity_name:
            localangle_entity_obj = localangle_entity_db_col.find_one({ 'name' : localangle_entity_name })
            for location in localangle_entity_obj['locations']:
                logging.debug('%s, %s %s' % (alchemyapi_entity['text'], location['state'], location['city']))
                yield {
                    'location' : location,
                    'entity' : {
                        'name' : alchemyapi_entity['text'],
                        'type' : alchemyapi_entity['type'],
                        'instances' : alchemyapi_entity['instances']
                    }
                }   

def update_contexts(incremental=True):
    localangle_person_names = dict([(person['name'], person['name']) for person in _db.persons.find()])
    localangle_company_names = collections.defaultdict(str, [(clean_company_name(company['name']), company['name']) for company in _db.companies.find()])
    
    story_criteria = { 'entities' : { '$exists' : True } }
    if incremental:
        story_criteria['contexts'] = { '$exists' : False }
    
    for story in _db.stories.find(story_criteria):
        
        contexts = []
        
        for entity in story['entities']:
            contexts += find_person_contexts(entity, localangle_person_names)
            contexts += find_company_contexts(entity, localangle_company_names)
            
        # Collapse by location
        story['contexts'] = []
        groupby_fn = lambda context: context['location']
        contexts.sort(key=groupby_fn)
        for location, location_contexts in itertools.groupby(contexts, key=groupby_fn):
            story['contexts'].append({
                'location' : location,
                'entities' : map(lambda context: context['entity'], location_contexts)
            })
        
        _db.stories.save(story)

def search_and_replace_text(source_text, search_text, replacement_pattern):
    
    if type(search_text) == list:
        to_search = search_text.pop(0)
    else:
        to_search = search_text
    
    pattern = re.compile('\\b(?P<token>%s)\\b' % to_search, flags=re.IGNORECASE)
    search = pattern.search(source_text)
    
    if search:
        return pattern.sub(replacement_pattern % search.group('token'), source_text, count=1)
    elif type(search_text) == list and any(search_text):
        return search_and_replace_text(source_text, search_text, replacement_pattern)
    else:
        return None

def transform_headlines_blurbs(incremental=True):
    alchemy = AlchemyAPI()

    PERSON_PATTERN = '<span class=\"context\">%s native %s</span>'
    COMPANY_PATTERN = '<span class=\"context\">%s-based %s</span>'

    story_criteria = { 'entities' : { '$exists' : True }, 'contexts' : { '$exists' : True, '$ne' : [] }}
    if incremental:
        story_criteria['contexts.headline'] = { '$exists' : False }
            
    for story in _db.stories.find(story_criteria):
        for context in story['contexts']:
            context['headline'] = None
            context['blurb'] = None
            
            display_location = context['location']['city'] if context['location']['city'] else context['location']['state']
            
            for entity in context['entities']:
                
                # Transform headlines
                if entity['type'] == 'Person':
                    new_headline = search_and_replace_text(story['titleNoFormatting'], [entity['name'], entity['name'].split()[-1]], PERSON_PATTERN % (display_location, '%s'))
                    new_blurb = search_and_replace_text(story['content'], entity['name'], PERSON_PATTERN % (display_location, '%s'))
                elif entity['type'] == 'Company':
                    new_headline = search_and_replace_text(story['titleNoFormatting'], [entity['name'], clean_company_name(entity['name'], robust=True)], COMPANY_PATTERN % (display_location, '%s'))
                    new_blurb = search_and_replace_text(story['content'], entity['name'], COMPANY_PATTERN % (display_location, '%s'))
                    
                if new_headline:
                    logging.debug(new_headline)
                    context['headline'] = new_headline
                    
                if new_blurb:
                    context['blurb'] = new_blurb
                
                # Transform "blurbs" 
                entity['instances'] = list((e['instances'] for e in story['entities'] if e['text'] == entity['name']).next())
                for i, instance in enumerate(entity['instances']):
                    if entity['type'] == 'Person':
                        entity['instances'][i] = search_and_replace_text(instance, entity['name'], PERSON_PATTERN % (display_location, '%s'))
                    elif entity['type'] == 'Company':
                        entity['instances'][i] = search_and_replace_text(instance, entity['name'], COMPANY_PATTERN % (display_location, '%s'))
            
        _db.stories.save(story)

"""
def rewrite_with_entity_location(text, entity, display_location, clean_entity_name=True):
    entity_pattern = re.compile('\\b(?P<entity>%s)\\b' % (clean_company_name(entity, robust=True) if clean_entity_name else entity), flags=re.IGNORECASE)
    entity_search = entity_pattern.search(text)
    if entity_search:
        return entity_pattern.sub('<span class=\"context\">%s-based %s</span>' % (display_location, entity_search.group('entity')), text)
    return None
"""