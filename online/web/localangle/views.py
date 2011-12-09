# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from pymongo import Connection, DESCENDING, ASCENDING
from collections import defaultdict

def init_db_connection():
    return Connection()['localangle']

def index(request):
    db = init_db_connection()
    locations = defaultdict(int)
    for story in db.stories.find():
        for context in story['contexts']:
            locations[context['location']] += 1
    return render_to_response('index.html', { 'locations' : [{ 'location' : location, 'count' : locations[location] } for location in sorted(locations)] })
    
def news(request, location):
    db = init_db_connection()
    stories = db.stories.find({ 'contexts' : { '$elemMatch' : { 'location' : location }}}).sort('publishedDate', direction=ASCENDING)
    return render_to_response('news.html', { 'location' : location, 'stories' : stories })
