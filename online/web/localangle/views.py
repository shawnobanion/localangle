# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from pymongo import Connection, DESCENDING, ASCENDING
from collections import defaultdict
import dateutil.parser

def init_db_connection():
    return Connection()['localangle']

def index(request):
    db = init_db_connection()
    locations = defaultdict(int)
    for story in db.stories.find({ 'contexts' : { '$exists' : True }}):
        for context in story['contexts']:
            locations[context['location']] += 1
    return render_to_response('index.html', { 'locations' : [{ 'location' : location, 'count' : locations[location] } for location in sorted(locations)] })
    
def news(request, location):
    db = init_db_connection()
    stories = db.stories.find({ 'contexts.location' : location }).sort('date', direction=DESCENDING)
    return render_to_response('news.html', {
        'location' : location,
        'stories' : map(lambda story: to_story(story, location), stories)
        })

def to_story(story, location):
    return {
        'image' : story['image'] if 'image' in story else None,
        'unescapedUrl' : story['unescapedUrl'],
        'titleNoFormatting' : story['titleNoFormatting'],
        'date' : story['date'],
        'content' : story['content'],
        'context' : (context for context in story['contexts'] if context['location'] == location).next()
    }