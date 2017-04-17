'''
Created on Mar 20, 2017

@author: I076054

'''
import urllib2
from bs4 import BeautifulSoup

def parsePage(url):
    page = urllib2.urlopen(url)
    html_doc = page.read()
    soup = BeautifulSoup(html_doc.decode('utf-8','ignore'), "html.parser")
    spans = soup.find_all('span', {'class':'num'})
    
    try:
        if len(spans) == 3:
            findAvg=None
        else:
            findAvg = spans[0].get_text()
    except:
        return (soup, None, None, None, None)
    if findAvg == None:
        avgPrice = "0"
        sailCount = spans[0].get_text()
        in90 = spans[1].get_text()
        viewCount = spans[2].get_text()
    else:    
        avgPrice = findAvg
        sailCount = spans[1].get_text()
        in90 = spans[2].get_text()
        viewCount = spans[3].get_text()
    return (soup, avgPrice, sailCount, in90, viewCount)