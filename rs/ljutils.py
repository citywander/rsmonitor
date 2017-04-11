'''
Created on Mar 20, 2017

@author: I076054

'''
import urllib2
import yaml
import socket
import json
import mysql.connector
import datetime
from bs4 import BeautifulSoup

def parsePage(url):
    page = urllib2.urlopen(url)
    html_doc = page.read()
    soup = BeautifulSoup(html_doc.decode('utf-8','ignore'), "html.parser")
    spans = soup.find_all('span', attrs={'class':'botline'})
    
    if len(spans) != 4:
        pass
    try:
        print url
        findAvg = spans[0].find("strong")
    except:
        return (soup, None, None, None, None)
    if findAvg == None:
        avgPrice = "0"
        sailCount = "0"
        in90 = "0"
        viewCount = "0"
    else:    
        avgPrice = findAvg.text
        sailCount = spans[1].find("strong").text
        in90 = spans[2].find("strong").text
        viewCount = spans[3].find("strong").text
    return (soup, avgPrice, sailCount, in90, viewCount)