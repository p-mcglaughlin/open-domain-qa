from page import Page
from cleaner import Cleaner
import bz2
import urllib
import xml.etree.ElementTree as ET

class WikiReader:
    _banned_title_groups = {'Category', 'Draft', 'File', 'Help', 'Template', 'Wikipedia'}
    
    def __init__(self, 
                 page_xml_file_path: str,
                 stream_offsets_file_path: str,
                 read_block_size: int=622144,
                 cleaner: 'Cleaner'=None
        ):
        #print(stream_offsets_file_path)
        self.page_xml_file_path = page_xml_file_path
        self.stream_offsets = WikiReader._get_stream_offsets(stream_offsets_file_path)
        self.read_block_size = read_block_size
        self.cleaner = cleaner
    
    def get_raw_text(self, stream_offset: int) -> str:
        with open(self.page_xml_file_path, 'rb') as f:
            unzipper = bz2.BZ2Decompressor()
            f.seek(stream_offset)
            raw_text = ['<data>']
            EOF = False  # just read entire stream = 100 articles (<5 MB of text)
            while not EOF:
                try:
                    block = f.read(self.read_block_size)
                    raw_text.append(unzipper.decompress(block).decode('utf-8'))
                except EOFError:
                    EOF = True
            raw_text.append('</data>')
            raw_text = ''.join(raw_text)
            return raw_text
    
    @staticmethod
    def is_redirect_or_banned_title_group(page_xml: ET.ElementTree) -> bool:
        if page_xml.find('redirect') is not None:
            return True
        title = page_xml.find('title').text
        if title[:title.find(':')] in WikiReader._banned_title_groups:
            return True
        return False
    
    def convert_raw_text_to_pages(self, raw_text: str) -> list['Page']:
        '''
        convert article from xml to cleaned text 
        '''
        root = ET.fromstring(raw_text)  # xml element tree
        pages = []
        for page_xml in root:
            if WikiReader.is_redirect_or_banned_title_group(page_xml):
                continue
            page_id = page_xml.find('id').text
            title = page_xml.find('title').text
            text = page_xml.find('revision').find('text').text
            if self.cleaner:
                text = self.cleaner.clean_text(text)
            page = Page(page_id, title, text)
            pages.append(page)
        return pages
    
    def get_pages(self, i: int) -> list['Page']:
        offset = self.stream_offsets[i]
        raw_text = self.get_raw_text(offset)
        return self.convert_raw_text_to_pages(raw_text)
    
    def num_streams(self) -> int:
        return len(self.stream_offsets)
    
    @classmethod
    def _get_stream_offsets(cls, stream_offsets_file_path: str) -> list[int]:
        with open(stream_offsets_file_path, 'r') as f:
            stream_offsets = [int(x) for x in f.read().split('\n') if len(x) > 0]
            return stream_offsets
    
    @classmethod
    def create_stream_offsets(cls, index_read_path: str, write_path: str):
        with open(index_read_path, 'rb') as f:
            unzipper = bz2.BZ2Decompressor()
            data = f.read()
            data = unzipper.decompress(data).decode('utf-8')
            indexs = [int(d.split(':')[0]) for d in data.split('\n') if len(d) > 0]
            index_set = list(sorted(set(indexs)))
            
        offsets = [str(i)+'\n' for i in index_set]
        with open(write_path, 'w') as f:
            f.writelines(offsets)
    
    @classmethod
    def from_urls(cls, stream_index_url: str, stream_xml_url: str) -> 'WikiReader':
        stream_path = './data/xml_stream.bz2'
        index_path = './data/index.bz2'
        offsets_path = './data/offsets.txt'
        try:
            urllib.request.urlretrieve(stream_xml_url, filename = stream_path)
            urllib.request.urlretrieve(stream_index_url, filename = index_path)
        except Exception as e:
            print('error: ', e)
        
        WikiReader.create_stream_offsets(index_path, offsets_path)
        reader = WikiReader(stream_path, offsets_path, cleaner = Cleaner())
        return reader
    
if __name__ == "__main__":
    offsets_raw = '/Users/Pete/Documents/wikipedia_stuff/compressed_data/enwiki-20250301-pages-articles-multistream-index1.txt-p1p41242.bz2'
    xml_path = '/Users/Pete/Documents/wikipedia_stuff/compressed_data/enwiki-20250301-pages-articles-multistream1.xml-p1p41242.bz2'
    offsets_path = 'offsets.txt'
    
    #WikiReader.create_stream_offsets(offsets_raw, offsets_path)
    
    cleaner = Cleaner()
    wiki = WikiReader(xml_path, offsets_path, cleaner=cleaner)
    a = wiki.get_pages(0)

    #base = 'https://dumps.wikimedia.org/enwiki/20250301/'
    #index = 'enwiki-20250301-pages-articles-multistream-index2.txt-p41243p151573.bz2'
    #xml = 'enwiki-20250301-pages-articles-multistream2.xml-p41243p151573.bz2'
    #reader = WikiReader.from_urls(base+index, base+xml)
    #a = reader.get_pages(0)



        
        
    
        
    