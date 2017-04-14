'''
Created on Mar 20, 2017

@author: I076054

'''
from bs4 import BeautifulSoup
from influxdb import InfluxDBClient
import urllib2
import yaml
import socket
import json
import ljutils

access_token="7poanTTBCymmgE0FOn1oKp"


def load():
    f = open('cities.yml')
    x = yaml.load(f)
    return x  

settings= load()

houseTemplates=[]

def parsePage(client, url, cityName, distinct = "all", area = "all", village = "all"):
    (soup, avgPrice, sailCount, in90, viewCount)=ljutils.parsePage(url)
    if avgPrice is None:
        return soup
    houseTemplate={}
    houseTemplate["measurement"]="PropertySales"
    tags={}
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
    if village == "all":
        tags["village"] = settings["words"]["all"]
    else:
        tags["village"] = village          
    houseTemplate["tags"]  = tags
    fields = {}
    
    fields["avgPrice"] = int(avgPrice)
    fields["sailCount"] = int(sailCount)
    fields["in90"] = int(in90)
    fields["viewCount"] = int(viewCount)
    houseTemplate["fields"]  = fields
    houseTemplates.append(houseTemplate)
    if len(houseTemplates) == 10:
        client.write_points(houseTemplates)
        houseTemplates=[]    
    return soup
    
def parseDistinct(soup, client, city):
    divs = soup.find_all('div', attrs={'class':'level1'})
    if len(divs) == 0:
        return
    for a in divs[0].find_all('a', attrs={'class':''}):
        baseUrl = "http://" + city["lj"] + ".lianjia.com/ershoufang/" + a["gahref"]
        soup = parsePage(client, baseUrl, city["name"], a.get_text().encode("utf-8"))
        parseArea(soup, client, city, a.get_text().encode("utf-8"))
    pass

def parseArea(soup, client, city, distinct = "all"):
    divs = soup.find_all('div', attrs={'class':'gio_plate'})
    if len(divs) == 0:
        return
    for a in divs[0].find_all('a', attrs={'class':''}):
        baseUrl = "http://" + city["lj"] + ".lianjia.com/ershoufang/" + a["gahref"]
        area = a.get_text().encode("utf-8")
        parsePage(client, baseUrl, city["name"], distinct, area)
        parseVillage(client, city, distinct, area, a["gahref"])
    pass

def parseCity(client, city):
    baseUrl = "http://" + city["lj"] + ".lianjia.com/ershoufang/"
    soup = parsePage(client, baseUrl, city["name"])
    parseDistinct(soup, client, city)
    pass

def parseMap(city, distinct):    
    url="http://soa.dooioo.com/api/v4/online/house/ershoufang/listMapResult?access_token=%s&client=pc&cityCode=%s&type=village&dataId=%s&limit_count=10000"
    url = url % (access_token, city, distinct)
    page = urllib2.urlopen(url)
    return json.load(page)["dataList"]
    
def parseVillage(client, city, distinct, area, distinctCode):
    villages = parseMap(city["lj"], distinctCode)
    for village in villages:
        baseUrl = "http://" + city["lj"] + ".lianjia.com/ershoufang/q" + village["dataId"]
        parsePage(client, baseUrl, city["name"], distinct, area, village["showName"])
    pass

if __name__ == '__main__':
    hostname = socket.gethostname()
    if hostname == "WAGAN":
        client = InfluxDBClient('127.0.0.1', 8086, '', '', 'RealEstate')
    else:
        client = InfluxDBClient('10.58.80.214', 8086, '', '', 'RealEstate')
    for city in settings["cities"]:
        parseCity(client, city)
        pass
    if len(houseTemplates) > 0:
        client.write_points(houseTemplates)    
    pass