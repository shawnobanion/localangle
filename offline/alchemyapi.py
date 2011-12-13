import urllib, urllib2
import json
from nltk import sent_tokenize
import re

class AlchemyAPI():
    
    def __init__(self, apikey='2218dba9d181d8e3874695743a35aabfcb4c0025'):
        self.apikey = apikey
           
    def _fetch(self, url):
        return urllib2.urlopen(url)
        
    def _get_params(self):
        return {
            'apikey' : self.apikey,
            'outputMode' : 'json',
            'showSourceText' : '1'
        }
    
    def analyze_text(self, text):
        params = self._get_params()
        params['text'] = text
        url = 'http://access.alchemyapi.com/calls/text/TextGetRankedNamedEntities?%s' % urllib.urlencode(params)
        response = json.load(self._fetch(url))        
        return response
    
    def analyze_url(self, url):
        params = self._get_params()
        params['url'] = url
        url = ' http://access.alchemyapi.com/calls/url/URLGetRankedNamedEntities?%s' % urllib.urlencode(params)
        response = json.load(self._fetch(url))
               
        
        for entity in response['entities']:
            entity['instances'] = []
        
        for sentence in sent_tokenize(response['text']):
            for entity in response['entities']:
                if re.search('\\b%s\\b' % self._escape_special_chars(entity['text']), sentence):
                    entity['instances'].append(sentence)
        
        return response
    
    def _escape_special_chars(self, text):
        result = ''
        text = text.strip('.!?(),')
        for char in text:
            if re.match('[^A-Za-z0-9 ]', char):
                result += '\\'
            result += char
        return result
            