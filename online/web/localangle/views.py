# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from pymongo import Connection, DESCENDING, ASCENDING
from collections import defaultdict
import dateutil.parser
import datetime

def init_db_connection():
    return Connection()['localangle']

def index(request):
    db = init_db_connection()
    
    #locations = defaultdict(int)
    #for story in db.stories.find({ 'contexts' : { '$exists' : True }}):
    #    for context in story['contexts']:
    #        locations[context['location']] += 1
    #return render_to_response('index.html', { 'locations' : [{ 'location' : location, 'count' : locations[location] } for location in sorted(locations)] })
    
    #return render_to_response('index.html', { 'locations' : db.stories.distinct('contexts.location') })
    
    new_threshold = datetime.datetime.now() - datetime.timedelta(hours=8)
    
    return render_to_response('index.html', {
        'locations' : [ {
            'location' : location,
            'count' : db.stories.find({ 'contexts.location.city' : location['city'], 'contexts.location.state' : location['state'] }).count(),
            'new' : db.stories.find({ 'contexts.location.city' : location['city'], 'contexts.location.state' : location['state'] }).sort('date', direction=DESCENDING).limit(1).next()['date'] > new_threshold
            } for location in db.stories.distinct('contexts.location')]
            })
    
def news(request, state, city=None):
    db = init_db_connection()
    story_criteria = { 'contexts.location.state' : state }
    if city:
        story_criteria['contexts.location.city'] = city
    
    stories = db.stories.find(story_criteria).sort('date', direction=DESCENDING).limit(16)
    return render_to_response('news.html', {
        'state' : state,
        'city' : city,
        'stories' : map(lambda story: to_story(story, state, city), stories)
        })

def to_story(story, state, city):
    return {
        'image' : story['image'] if 'image' in story else None,
        'unescapedUrl' : story['unescapedUrl'],
        'titleNoFormatting' : story['titleNoFormatting'],
        'date' : story['date'],
        'content' : story['content'],
        'context' : (context for context in story['contexts'] if context['location']['state'] == state and (not city or context['location']['city'] == city)).next()
    }