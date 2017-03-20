'''
Created on Mar 20, 2017

@author: I076054

'''
from bs4 import BeautifulSoup
from influxdb import InfluxDBClient
import urllib2

def viewCount(url):
    page = urllib2.urlopen(url)
    html_doc = page.read()
    soup = BeautifulSoup(html_doc.decode('utf-8','ignore'), "html.parser")
    spans = soup.find_all('span', attrs={'class':'botline'})
    if len(spans) != 4:
        pass
    avgPrice = spans[0].find("strong").text
    sellCount = spans[1].find("strong").text
    dealedCount = spans[2].find("strong").text
    viewedCount = spans[3].find("strong").text
    print avgPrice, sellCount, dealedCount, viewedCount
    
        #print span.find_all("strong")
    pass

if __name__ == '__main__':
    viewCount("http://sh.lianjia.com/ershoufang/")
    client = InfluxDBClient('10.58.80.137', 8086, '', '', 'realestate')
    json_body = [
    {
        "measurement": "summary",
        "tags": {
            "city": "city",
            "zone": "zone",    
        },
        "time": "2009-11-10T23:00:00Z",
        "fields": {
            "value": 0.64
        }
    }
]
    pass