#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 11 23:18:52 2025

@author: Pete
"""

from bs4 import BeautifulSoup
import requests

def save_links(links, path):
    with open(path, 'w') as f:
        for link in links:
            f.write(link)
            f.write('\n')

if __name__ == "__main__":
    xml_path = 'xml_links.txt'
    index_path = 'index_links.txt'
    url = 'https://dumps.wikimedia.org/enwiki/20250301/'
    html = requests.get(url).content
    soup = BeautifulSoup(html, 'html.parser')
    
    xml_links, index_links = [], []
    for link in soup.find_all('a'):
        l = link.get('href')
        if l.find('articles-multistream') >= 0:
            if l.find('xml') >= 0:
                xml_links.append(l)
            else:
                index_links.append(l)
    xml_links = xml_links[1:]
    index_links = index_links[1:]
    
    mismatch = []
    for i in range(1, len(xml_links)):
        j = xml_links[i].rfind('-')
        k = index_links[i].rfind('-')
        if xml_links[i][j:] != index_links[i][k:]:
            mismatch.append(i)
    
    save_links(xml_links, xml_path)
    save_links(index_links, index_path)
        
    
        