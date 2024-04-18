import logging
import re
import sys
from bs4 import BeautifulSoup
from queue import Queue
from urllib import parse, request
from urllib.parse import urlparse
import heapq
from urllib.robotparser import RobotFileParser
from selenium import webdriver 

logging.basicConfig(level=logging.DEBUG, filename='output.log', filemode='w')
visitlog = logging.getLogger('visited')
extractlog = logging.getLogger('extracted')

def relevance_by_depth(url):
    return url.count('/')


def parse_links_sorted(root, html):
    links = list(parse_links(root, html))

    heap = []

    for link in links:
        score = relevance_by_depth(link[0])
        heapq.heappush(heap, (score, link[0]))

    return heap


def parse_links(root, html):
    


    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            text = link.string
            if not text:
                text = ''
            text = re.sub('\s+', ' ', text).strip()
            yield (parse.urljoin(root, link.get('href')), text) #HERE



def get_links(url):
    driver = webdriver.Chrome() # using Selenium 
    driver.get(url) #link to scrape 
    res = driver.page_source

    #res = request.urlopen(url)
    driver.quit() #selenium

    return list(parse_links(url, res))

def is_self_referencing_link(url, link): #check if this is right
    end_of_link = url.rsplit('/', 1)[-1]
    return end_of_link in link
    

def get_nonlocal_links(url, rp):
    '''Get a list of links on the page specificed by the url,
    but only keep non-local links and non self-references.
    Return a list of (link, title) pairs, just like get_links()'''

    # TODO: implement
    domain = ""
    links = get_links(url)
    filtered = []

    for link, title in links: 
        if not rp.can_fetch("*", link):
            continue
        if urlparse(link).netloc != domain:
            if not is_self_referencing_link(url, link):
                filtered.append((link, title))
    return filtered

    ## test remove
    """ if ("http" in url):
        if("www." in url[0:12]):
            index_of_dot = url.find(".", 7)
            if ("/" in url[11:]):
                index_of_slash = url.find("/", 11)
                domain = url[index_of_dot + 1:index_of_slash]
            else:
                domain = url[index_of_dot + 1:]
        else:
            index_of_first = url[0:8].rfind('/') + 1
            if ("/" in url[8:]):
                index_of_slash = url.find("/", 8)
                domain = url[index_of_first:index_of_slash]
            else:
                domain = url[index_of_first:] 


    
    links = get_links(url)
    filtered = []

    for link, title in links: 
        if ("http" in link):
            if("www." in link[0:12]):
                index_of_dot = link.find(".", 7)
                if ("/" in link[11:]):
                    index_of_slash = link.find("/", 11)
                    new_domain = link[index_of_dot + 1:index_of_slash]
                else:
                    new_domain = link[index_of_dot + 1:]
            else:
                index_of_first = link[0:8].rfind('/') + 1
                if ("/" in link[8:]):
                    index_of_slash = link.find("/", 8)
                    new_domain = link[index_of_first:index_of_slash]
                else:
                    new_domain = link[index_of_first:]
        
        if (new_domain != domain):
            if not is_self_referencing_link(url, link):
                filtered.append((link, title))
                
        #ask if we should do error handling if https is not present
        #do we have to check if links we've extracted from url are self-referencing of each other, 
        #or is checking that its not self referencing with the url is fine
    
    return filtered 
    """

def is_within_domain(url, link):

    return urlparse(url).netloc == urlparse(link).netloc
    
    #test rm 
    domain = ""

    if ("http" in url):
        if("www." in url[0:12]):
            index_of_dot = url.find(".", 7)
            if ("/" in url[11:]):
                index_of_slash = url.find("/", 11)
                domain = url[index_of_dot + 1:index_of_slash]
            else:
                domain = url[index_of_dot + 1:]
        else:
            index_of_first = url[0:8].rfind('/') + 1
            if ("/" in url[8:]):
                index_of_slash = url.find("/", 8)
                domain = url[index_of_first:index_of_slash]
            else:
                domain = url[index_of_first:]

    if ("http" in link):
        if("www." in link[0:12]):
            index_of_dot = link.find(".", 7)
            if ("/" in link[11:]):
                index_of_slash = link.find("/", 11)
                new_domain = link[index_of_dot + 1:index_of_slash]
            else:
                new_domain = link[index_of_dot + 1:]
        else:
            index_of_first = link[0:8].rfind('/') + 1
            if ("/" in link[8:]):
                index_of_slash = link.find("/", 8)
                new_domain = link[index_of_first:index_of_slash]
            else:
                new_domain = link[index_of_first:]
            
        if (new_domain == domain):
            return True
        else: 
            return False

def crawl(root, rp, wanted_content=[], within_domain=True):
    '''Crawl the url specified by `root`.
    `wanted_content` is a list of content types to crawl
    `within_domain` specifies whether the crawler should limit itself to the domain of `root`
    '''
    # TODO: implement

    queue = Queue()
    queue.put(root)

    visited = []
    extracted = []

    while not queue.empty(): #and len(visited) < 200
        url = queue.get()
        try:
            if not rp.can_fetch("*", url):
                continue
            req = request.urlopen(url)
            html = req.read()

            if url not in visited:
                visited.append(url)
                visitlog.debug(url)

                #test uncomment    
                for ex in extract_information(url, html):
                    extracted.append(ex)
                    extractlog.debug(ex)

                for link, title in parse_links(url, html):
                    if not is_self_referencing_link(url, link): 
                        if within_domain and is_within_domain(url, link):
                            if len(wanted_content) == 0: 
                                queue.put(link)
                            elif len(wanted_content) > 0 and req.headers['Content-Type'] in wanted_content:
                                queue.put(link)                

                    soup = BeautifulSoup(html, 'html.parser')
                    div = soup.find('div', class_='mt-2 lead-sm html-data')
                    if div:
                        text = div.text.strip()
                        extracted.append((url, 'HTML_DATA', text))
                    for link, title in parse_links(url, html):
                        if not is_self_referencing_link(url, link): 
                            if within_domain and is_within_domain(url, link):
                                if len(wanted_content) == 0: 
                                    queue.put(link)
                                elif len(wanted_content) > 0 and req.headers['Content-Type'] in wanted_content:
                                    queue.put(link)                


        except Exception as e:
            print(e, url)

    return visited, extracted


def extract_information(address, html):
    '''Extract contact information from html, returning a list of (url, category, content) pairs,
    where category is one of PHONE, ADDRESS, EMAIL'''

    # TODO: implement
    results = []
    for match in re.findall('\d\d\d-\d\d\d-\d\d\d\d', str(html)):
        results.append((address, 'PHONE', match))
    
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', str(html))
    for email in emails:
        results.append((address, 'EMAIL', email))

    addresses1 = re.findall(r'\b\w+\s?,?\s\w+(?:\s\w+)?\s\d{5}\b', str(html))
    for address1 in addresses1:
        results.append((address, 'ADDRESS', address1))

    return results


def writelines(filename, data):
    with open(filename, 'w') as fout:
        for d in data:
            print(d, file=fout)


def main():

    site = sys.argv[1]

    rp = RobotFileParser()
    rp.set_url(parse.urljoin(site, '/robots.txt'))
    rp.read()

    links = get_links(site)
    writelines('links.txt', links)

    nonlocal_links = get_nonlocal_links(site, rp)
    writelines('nonlocal.txt', nonlocal_links)

    visited, extracted = crawl(site, rp)
    writelines('visited.txt', visited)
    writelines('extracted.txt', extracted)


if __name__ == '__main__':
    main()
    #test("https://www.cs.jhu.edu/~yarowsky/cs466.html")

    #implement parse_links_sorted
    #fix email detection