import urllib2
from BeautifulSoup import BeautifulSoup
import re

class CategoryScraper:
    
    def __init__(self):
        pass
    
    def _fetch(self, url):
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        return opener.open(url).read()
    
    def scrape_subcategories(self, url):
        return self._scrape_category(url, 'mw-subcategories', self._parse_lineitems_with_pages_and_urls, graceful=True)
            
    def _parse_lineitems_with_pages_and_urls(self, container):
        lineitems = []
        for li in container.findAll('li'):
            span = li.findAll('span')[-1]
            # Check to see if this subcategories has > 0 pages associated with it
            title_search = re.search('(\d+) page', span['title'])
            if title_search and int(title_search.group(1)) > 0:
                a = li.find('a')
                lineitems.append((a.contents[0], 'http://en.wikipedia.org' + a['href']))
        return lineitems
        
    def scrape_pages(self, url):
        return self._scrape_category(url, 'mw-pages', self._parse_lineitems)
        
    def _parse_lineitems(self, container):
        return map(lambda tag: tag.contents[0], container.findAll('a'))
    
    def _scrape_category(self, url, container_id, lineitem_parser, graceful=False):
        html = self._fetch(url)        
        doc = BeautifulSoup(html)
                
        #pages_header = doc.find('h2', text=re.compile(h2pattern))
        #if graceful and not pages_header:
        #    return []
        #pages_container = pages_header.findNext('div')
        
        container = doc.find('div', id=container_id) # This encomposes the "subcategory" or "pages" portion of the page
        if graceful and not container:
            return []
        inner_container = container.find('div') # This holds all of the "pages" and links
        
        # Check to see if the pages roll over to another page
        next_page = container.find('a', text='next 200')
        # If so, get the URL of the 'next' link
        if next_page:
            for anchor in container.findAll('a'):
                if any(anchor.contents) and anchor.contents[0] == 'next 200':
                    next_page_url = anchor['href']
                    break

        lineitems = lineitem_parser(inner_container)
        
        if not next_page:
            return lineitems
        else:
            return lineitems + self._scrape_category('http://en.wikipedia.org/' + next_page_url, container_id, lineitem_parser)
            
    