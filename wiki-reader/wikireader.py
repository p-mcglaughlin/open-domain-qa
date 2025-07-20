from page import Page
from cleaner import Cleaner
import bz2, urllib
import xml.etree.ElementTree as ET

class WikiReader:
    # articles starting with these indentifiers are about how to create/use wikipedia pages so they are skipped
    _banned_title_groups = {'Category', 'Draft', 'File', 'Help', 'Template', 'Wikipedia'}
    
    def __init__(self, 
                 page_xml_file_path: str,
                 stream_offsets_file_path: str,
                 read_block_size: int=622144,
                 cleaner: 'Cleaner'=None
        ):
        '''
        Inputs:
            - page_xml_file_path: bz2 compressed multistream file of xml pages.
            - stream_offsets_file_path: .txt file containing unique file offset sorted in increasing order, 
                generate with _create_stream_offsets
            - read_block_size: file is blocks of read_block size bytes
            - cleaner: text cleaner to apply to text, if None returns raw xml files
        '''
        self.page_xml_file_path = page_xml_file_path
        self.stream_offsets = WikiReader._get_stream_offsets(stream_offsets_file_path)
        self.read_block_size = read_block_size
        self.cleaner = cleaner
    
    def _get_raw_text(self, stream_offset: int) -> str:
        '''
        extracts xml files from the bz2 compressed file starting at stream_offset
        returns xml element tree of the form:
            <data>
                <page>
                    page data
                </page>
                ...
                <page>
                    page data
                </page>
            </data>
        '''
        with open(self.page_xml_file_path, 'rb') as f:
            unzipper = bz2.BZ2Decompressor()
            f.seek(stream_offset)
            raw_text = ['<data>'] # wrap individual pages to make valid xml element tree
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
    def _is_redirect_or_banned_title_group(page_xml: ET.ElementTree) -> bool:
        '''
        check if this article should be skipped
        '''
        if page_xml.find('redirect') is not None: # this 'article' just redirects to something else
            return True
        title = page_xml.find('title').text
        if title[:title.find(':')] in WikiReader._banned_title_groups: # this is an article about creating or using wiki pages
            return True
        return False
    
    def _convert_raw_text_to_pages(self, raw_text: str) -> list['Page']:
        '''
        convert articles from xml to cleaned text 
        '''
        root = ET.fromstring(raw_text)  # xml element tree
        pages = []
        for page_xml in root:
            if WikiReader._is_redirect_or_banned_title_group(page_xml):
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
        '''
        returns cleaned text from the i'th stream in the file 
        (~100 articles depending # of redirects and other removed articles)
        '''
        offset = self.stream_offsets[i]
        raw_text = self._get_raw_text(offset)
        return self._convert_raw_text_to_pages(raw_text)
    
    def num_streams(self) -> int:
        '''
        return number of streams in this file
        '''
        return len(self.stream_offsets)
    
    @classmethod
    def _get_stream_offsets(cls, stream_offsets_file_path: str) -> list[int]:
        '''
        loads precomputed file offsets from stream_offsets_file_path
        '''
        with open(stream_offsets_file_path, 'r') as f:
            stream_offsets = [int(x) for x in f.read().split('\n') if len(x) > 0]
            return stream_offsets
    
    @classmethod
    def _create_stream_offsets(cls, index_read_path: str, write_path: str) -> None:
        '''
        extracts stream (file) offsets from the index file index_read_path
        writes the offsets as .txt file to write_path
        '''
        # index file consists of lines of the form:
        #       offset:page-id:page-title
        # we just want to get the sorted list of unique offsets
        with open(index_read_path, 'rb') as f:
            unzipper = bz2.BZ2Decompressor()
            data = f.read()
            data = unzipper.decompress(data).decode('utf-8')
            # d has the form- offset:page-id:page-title
            indexs = [int(d.split(':')[0]) for d in data.split('\n') if len(d) > 0]
            index_set = list(sorted(set(indexs)))
            
        offsets = [str(i)+'\n' for i in index_set]
        with open(write_path, 'w') as f:
            f.writelines(offsets)
    
    @classmethod
    def from_urls(cls, stream_index_url: str, stream_xml_url: str, write_location: str='./data') -> 'WikiReader':
        '''
        downloads index and xml files from: stream_index_url and stream_xml_url, respectively
        writes the data into {write_location}/xml_stream.bz2 and {write_location/index.bz2
        returns WikiReader object that can be used to extract cleaned text
        '''
        stream_path = f'{write_location}/xml_stream.bz2'
        index_path = f'{write_location}/index.bz2'
        offsets_path = f'{write_location}/offsets.txt'
        try:
            urllib.request.urlretrieve(stream_xml_url, filename = stream_path)
            urllib.request.urlretrieve(stream_index_url, filename = index_path)
        except Exception as e:
            print('error: ', e)
        
        WikiReader._create_stream_offsets(index_path, offsets_path)
        reader = WikiReader(stream_path, offsets_path, cleaner = Cleaner())
        return reader      
    
