import urllib, urllib2
import json

class GoogleNews():
    
    def __init__(self, apikey='ABQIAAAA3KojQYx0MefvIZXqPxrM3RT2yXp_ZAY8_ufC3CFXhHIE1NvwkxSqpWE4GSEtN42dt2Ui10RQdwVtiw'):
        self.apikey = apikey
        
    def _format_url(self, params):
        return 'https://ajax.googleapis.com/ajax/services/search/news?%s' % urllib.urlencode(params)
    
    def _fetch(self, url):
        return urllib2.urlopen(url)
        
    def _get_params(self):
        return {
            'v' : 1.0,
            'key' : self.apikey,
            'rsz' : '8'
         }
    
    def from_topic(self, topic):
        """
        h - specifies the top headlines topic
        w - specifies the world topic
        b - specifies the business topic
        n - specifies the nation topic
        t - specifies the science and technology topic
        el - specifies the elections topic
        p - specifies the politics topic
        e - specifies the entertainment topic
        s - specifies the sports topic
        m - specifies the health topic
        """
        params = self._get_params()
        params['topic'] = topic
        response = json.load(self._fetch(self._format_url(params)))
        return response['responseData']['results']