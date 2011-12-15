import re

def remove_punctuation(text):
    return re.sub('[^A-Z|a-z|\d|\s]', ' ', text).strip()

def clean_company_name(name, robust=False):
    name = remove_punctuation(name.lower())
    
    stop_list = [    
        'amp',
        'and',
        'co',
        'companies',
        'company',
        'corp',
        'corporation',
        'com',
        'communications',
        'entertainment',
        'group',
        'holdings',
        'inc',
        'l',
        'llc',
        'ltd',
        'p',
        'plc',
        'system',
        'systems',
        'technology',
        'the'
        ]
    
    if robust:
        stop_list += [
            'international',
            'securities',
            'software',
            'usa'
            ]
        
    name = ' '.join(filter(lambda word: word not in stop_list, name.split()))
    return name

def distinct_entity_companies():
    db = get_connection()
    companies = []
    for story in db.stories.find({ 'entities' : { '$exists' : True }}):
        for entity in story['entities']:
            if entity['type'] == 'Company':
                companies.append(entity['text'].lower())
    return sorted(list(set(companies)))