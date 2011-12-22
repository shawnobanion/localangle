# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from pymongo import Connection, DESCENDING, ASCENDING
from collections import defaultdict
import dateutil.parser
import datetime

_db = Connection()['localangle']

def index(request):
    return render_to_response('index.html', {
        'locations' : [ {
            'location' : location,
            'metadata' : get_metadata(location['city'], location['state']),
            #'count' : _db.stories.find({ 'contexts.location.city' : location['city'], 'contexts.location.state' : location['state'] }).count(),
            #'new' : _db.stories.find({ 'contexts.location.city' : location['city'], 'contexts.location.state' : location['state'] }).sort('date', direction=DESCENDING).limit(1).next()['date'] > new_threshold
            } for location in _db.stories.distinct('contexts.location')]
            })
    
def get_metadata(city, state):
    new_threshold = datetime.datetime.now() - datetime.timedelta(hours=8)
    isnew = False
    persons, companies = 0, 0
    
    story_criteria = { 'contexts.location.state' : state }
    if city:
        story_criteria['contexts.location.city'] = city
        
    for story in _db.stories.find(story_criteria):
        if story['date'] > new_threshold:
            isnew = True
        distinct_entity_types = set([entity['type'] for context in story['contexts'] for entity in context['entities'] if context['location']['city'] == city and context['location']['state'] == state])
        if 'Person' in distinct_entity_types:
            persons += 1
        if 'Company' in distinct_entity_types:
            companies += 1
    return {
        'persons' : persons,
        'companies' : companies,
        'isnew' : isnew
    }
        
def news(request, state, city=None):

    story_criteria = { 'contexts.location.state' : state }
    if city:
        story_criteria['contexts.location.city'] = city
    
    stories = map(lambda story: to_story(story, state, city), _db.stories.find(story_criteria))#.sort('date', direction=DESCENDING)) #.limit(16)
    stories.sort(key=lambda story: story['date'], reverse=True)
    stories.sort(key=lambda story: story['score'], reverse=True)
    
    return render_to_response('news.html', {
        'state' : state,
        'city' : city,
        'stories' : stories[:18]
        })

def to_story(story, state, city):
    context = (context for context in story['contexts'] if context['location']['state'] == state and (not city or context['location']['city'] == city)).next()
    score = 0
    if context['headline']: score += 10
    if context['blurb']: score += 5
    return {
        'image' : story['image'] if 'image' in story else None,
        'unescapedUrl' : story['unescapedUrl'],
        'titleNoFormatting' : story['titleNoFormatting'],
        'date' : story['date'],
        'content' : story['content'],
        'context' : context,
        'score' : score
    }