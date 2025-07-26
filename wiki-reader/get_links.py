from bs4 import BeautifulSoup
import requests

def save_links(links -> List[str], file_path: str):
    '''
    write the list of urls links to path
    '''
    f = '\n'.join(links)
    with open(file_path, 'w') as f:
        f.write(links)

if __name__ == "__main__":
    # full path you want to write xml urls to
    xml_path = 'xml_links.txt' 
    # full path you want to write index urls to
    index_path = 'index_links.txt' 
    # the date of the dump you want to use, e.g., 20250401
    # you can find available dumps at https://dumps.wikimedia.org/enwiki
    dump_date = '20240401'
    
    url = f'https://dumps.wikimedia.org/enwiki/{dump_date}/'
    html = requests.get(url).content
    soup = BeautifulSoup(html, 'html.parser')
    
    xml_links, index_links = [], []
    for link in soup.find_all('a'):
        l = link.get('href')
        # the name of xml and index files contain 'articles-multistream'
        # everything else is logging, meta data, etc.
        if l.find('articles-multistream') >= 0: 
            if l.find('xml') >= 0:
                xml_links.append(l)
            else:
                index_links.append(l)
    # the first urls will contain the entire dump (~24 GB compressed)
    # alternatively, you can get 60-70 files (~400 MB compressed each) shown below
    xml_links = xml_links[1:] 
    index_links = index_links[1:]
    # comment out the above and uncomment below to urls for 1 pair of (very large) files instead
    # xml_links, index_links = xml_links[0], index_links[0]
    
    save_links(xml_links, xml_path)
    save_links(index_links, index_path)
        
    
        
