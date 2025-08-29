import time
import warnings
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import requests
from urllib3.exceptions import NotOpenSSLWarning

# This line will suppress the specific SSL compatibility warning from urllib3
warnings.filterwarnings('ignore', category=NotOpenSSLWarning)

def get_session():
    """Returns a requests.Session object for making HTTP requests."""
    return requests.Session()

def is_same_domain(base_url, url):
    """Checks if a given URL is on the same domain as the base URL."""
    try:
        return urlparse(base_url).netloc == urlparse(url).netloc
    except ValueError:
        return False

def extract_links(html, page_url):
    """Extracts all absolute links from a given HTML string."""
    links = set()
    soup = BeautifulSoup(html, 'html.parser')
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href')
        absolute_url = urljoin(page_url, href)
        links.add(absolute_url)
    return list(links)

def extract_forms(html, page_url):
    """Extracts all forms from a given HTML string."""
    forms = []
    soup = BeautifulSoup(html, 'html.parser')
    for form_tag in soup.find_all('form'):
        form_info = {
            'method': form_tag.get('method', 'get').lower(),
            'action': urljoin(page_url, form_tag.get('action', '')),
            'inputs': []
        }
        for input_tag in form_tag.find_all(['input', 'textarea', 'select']):
            input_info = {
                'name': input_tag.get('name'),
                'type': input_tag.get('type'),
                'value': input_tag.get('value')
            }
            form_info['inputs'].append(input_info)
        forms.append(form_info)
    return forms

class Crawler:
    """A simple web crawler to find links and forms within a single domain."""
    def __init__(self, base_url, max_pages=200, delay=0.2, session=None):
        self.base = base_url.rstrip('/')
        self.max_pages = max_pages
        self.delay = delay
        self.session = session or get_session()
        self.visited = set()
        self.queue = [self.base]
        self.pages = {}
        self.forms = {}
        print(f"[*] Initializing crawler for base URL: {self.base}")
        print(f"[*] Max pages to crawl: {self.max_pages}, delay: {self.delay}s")

    def crawl(self):
        """Starts the crawling process."""
        while self.queue and len(self.visited) < self.max_pages:
            url = self.queue.pop(0).rstrip('/')
            
            print(f"\n[*] Processing URL: {url}")
            
            if url in self.visited or not is_same_domain(self.base, url):
                print(f"[*] Skipping {url} (already visited or different domain)")
                continue

            try:
                print(f"[*] Fetching content from: {url}")
                r = self.session.get(url, timeout=10, allow_redirects=True)
                r.raise_for_status() 
                
                self.pages[url] = r.text
                print(f"[+] Successfully fetched {url} (Status: {r.status_code})")
                
                forms = extract_forms(r.text, url)
                if forms:
                    self.forms[url] = forms
                    print(f"  [+] Found {len(forms)} form(s) on this page.")
                
                links = extract_links(r.text, url)
                print(f"  [+] Found {len(links)} link(s) on this page.")
                for l in links:
                    l = urldefrag(l)[0].rstrip('/')
                    if l and l not in self.visited and l not in self.queue:
                        self.queue.append(l)
                        print(f"    - Added new link to queue: {l}")

            except requests.exceptions.RequestException as e:
                print(f"[!] Failed to fetch {url}: {e}")
            
            except Exception as e:
                print(f"[!] An unexpected error occurred with {url}: {e}")

            finally:
                self.visited.add(url)
                print(f"[*] Visited pages count: {len(self.visited)}")
                time.sleep(self.delay)

        return {'pages': self.pages, 'forms': self.forms}


if __name__ == "__main__":
    print("--- Running Web Crawler Test ---")
    
    \
    base_url =  "http://127.0.0.1:3000/"
    
    
    my_crawler = Crawler(base_url=base_url, max_pages=5, delay=0.5)
    
    # Run the crawl
    print(f"\nStarting crawl of {base_url}...")
    results = my_crawler.crawl()
    
    # Print the final results of the crawl
    print("\n--- Crawl Results ---")
    print(f"Total unique pages visited: {len(results['pages'])}")
    print("Visited URLs:")
    for url in sorted(results['pages'].keys()):
        print(f" - {url}")

    # Check for forms and print their details
    if results['forms']:
        print("\nFound forms on the following pages:")
        for url, forms in results['forms'].items():
            print(f" - {url}:")
            for form in forms:
                print(f"   - Method: {form['method']}, Action: {form['action']}")
    else:
        print("\nNo forms were found during the crawl.")

    print("\n--- Test Complete ---")