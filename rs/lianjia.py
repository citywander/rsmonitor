'''
Created on Mar 20, 2017

@author: I076054

'''
from bs4 import BeautifulSoup
from influxdb import InfluxDBClient
import urllib2
import yaml


template = {
    "measurement": "RealEstate",
    "tags": {
        "agent": "",
        "city": "city",
        "distinct": "zone",    
        "area": ""
    },
    "fields": {
        "avgPrice": 1,
        "sailCount": 20,
        "in90": 20,
        "viewCount": 20
    }
}
    
def load():
    f = open('cities.yml')
    x = yaml.load(f)
    return x  

settings= load()

def parsePage(client, url, cityName, distinct = "all", area = "all"):
    page = urllib2.urlopen(url)
    html_doc = page.read()
    soup = BeautifulSoup(html_doc.decode('utf-8','ignore'), "html.parser")
    spans = soup.find_all('span', attrs={'class':'botline'})
   
    if len(spans) != 4:
        pass
    findAvg = spans[0].find("strong")
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
    tags=template["tags"]
    tags["agent"] = settings["agents"]["lj"]
    tags["city"] = cityName
    if distinct == "all":
        tags["distinct"] = settings["words"]["all"]
    else:
        tags["distinct"] = distinct
    if area == "all":
        tags["area"] = settings["words"]["all"]
    else:
        tags["area"] = area    
    fields=template["fields"]
    fields["avgPrice"] = int(avgPrice)
    fields["sailCount"] = int(sailCount)
    fields["in90"] = int(in90)
    fields["viewCount"] = int(viewCount)
    client.write_points([template])
    return soup
    
def parseDistinct(soup, client, city):
    divs = soup.find_all('div', attrs={'class':'gio_district'})
    if len(divs) == 0:
        return
    for a in divs[0].find_all('a', attrs={'class':''}):
        baseUrl = "http://" + city["lj"] + ".lianjia.com/ershoufang/" + a["gahref"]
        soup = parsePage(client, baseUrl, city["name"], a.get_text().encode("utf-8"))
        parseArea(soup, client, city, a.get_text().encode("utf-8"))
    pass

def parseArea(soup, client, city, distinct = "all", area = "all"):
    divs = soup.find_all('div', attrs={'class':'gio_plate'})
    if len(divs) == 0:
        return
    for a in divs[0].find_all('a', attrs={'class':''}):
        print a
        baseUrl = "http://" + city["lj"] + ".lianjia.com/ershoufang/" + a["gahref"]
        parsePage(client, baseUrl, city["name"], distinct, a.get_text().encode("utf-8"))
    pass

def parseCity(client, city):
    baseUrl = "http://" + city["lj"] + ".lianjia.com/ershoufang/"
    soup = parsePage(client, baseUrl, city["name"])
    parseDistinct(soup, client, city)
    pass
    
if __name__ == '__main__':
    client = InfluxDBClient('10.58.80.137', 8086, '', '', 'RealEstate')
    for city in settings["cities"]:
        parseCity(client, city)
        pass
    #result = client.query('select * from "RealEstate";')
    #print result
    pass