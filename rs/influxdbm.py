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
from threading import Thread, Lock
from influxdb import InfluxDBClient

add_daily = ("INSERT INTO daily "
              "(rec_date)"
              "VALUES (%(rec_date)s)")

add_village_daily = ("INSERT INTO village_inf "
              "(avgPrice, in90, sailCount, viewCount, city,area,district,village,rec_time)"
              "VALUES (%(avgPrice)s, %(in90)s, %(sailCount)s,%(viewCount)s,%(city)s, %(area)s, %(district)s, %(village)s,%(rec_time)s)")

def load():
    f = open('cities.yml')
    x = yaml.load(f)
    return x  

settings= load()

def getVillages(cursor):
    villages={}
    query = ("SELECT id, name FROM village")
    cursor.execute(query)
    for (id, name) in cursor:
        villages[name.encode("utf-8")]=id
    return villages

def getAreas(cursor):
    areas={}
    query = ("SELECT id, name FROM area")
    cursor.execute(query)
    for (id, name) in cursor:
        areas[name.encode("utf-8")]=id
    return areas

def getDistricts(cursor):
    districts={}
    query = ("SELECT id, name from district")
    cursor.execute(query)
    for (id, name) in cursor:
        districts[name.encode("utf-8")]=id
    return districts

def getRecordDate(cursor):
    id = getLatestRecordDate(cursor)
    if id != None:
        return id
    now = datetime.datetime.now()
    data_date = {
      'rec_date': now.strftime('%Y-%m-%d %H:%M:%S')
    }
    cursor.execute(add_daily, data_date)
    conn.commit()
    return getLatestRecordDate(cursor)

def getLatestRecordDate(cursor):
    now = datetime.datetime.now()
    query="SELECT id FROM realestate.daily where rec_date > '" + now.strftime('%Y-%m-%d') + " 00:00'"
    cursor.execute(query)
    for (id,) in cursor:
        return id
    return None
    
def parsePage(url, villageId, code, cursor, daily_id):
    page = urllib2.urlopen(url)
    html_doc = page.read()
    soup = BeautifulSoup(html_doc.decode('utf-8','ignore'), "html.parser")
    spans = soup.find_all('span', attrs={'class':'botline'})
   
    if len(spans) != 4:
        pass
    try:
        findAvg = spans[0].find("strong")
    except:
        print url
        return soup
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
    data_daily = {
        "avgPrice": avgPrice,
        "in90": in90,
        "sailCount": sailCount,
        "viewCount": viewCount,
        "village_id": villageId,
        "daily_id": daily_id
    } 
    cursor.execute(add_village_daily, data_daily)
    conn.commit()   
    return soup

def getVillageDaily(cursor, dailyId):
    villageIds=set()
    query = ("SELECT village_id FROM village_daily where daily_id=" + str(dailyId))
    cursor.execute(query)
    for(villageId,) in cursor:
        villageIds.add(villageId)
    return villageIds

def recordDaily(cursor, dailyId):
    villages = getVillages(cursor)
    villageIds=getVillageDaily(cursor, dailyId)
    for (code, villageId) in villages.items():
        if villageId in villageIds:
            continue
        baseUrl = "http://sh.lianjia.com/ershoufang/q" + code
        parsePage(baseUrl, villageId, code, cursor, dailyId)
    pass

def getHouses(cursor):
    houses={}
    query = ("SELECT id, code FROM house where saled_date is not null")
    cursor.execute(query)
    for (id, code) in cursor:
        houses[code]=id
    return houses

def parseHousePage(url,code, cursor):
    page = urllib2.urlopen(url)
    html_doc = page.read()
    soup = BeautifulSoup(html_doc.decode('utf-8','ignore'), "html.parser")
    xiajia = soup.find_all('div', attrs={'class':'tag tag_yixiajia'})
    yishixiao = soup.find_all('div', attrs={'class':'tag tag_yishixiao'})
    if len(xiajia) > 0 or len(yishixiao)>0:
        return
    #updateSql="update realestate.house set saled_date=null where code='" + code + "'" 
    #cursor.execute(updateSql)
    #conn.commit()    

def influxToDb():
    influxSql="SELECT * FROM HouseSales"
    result = client.query(influxSql, database="RealEstate")           
    villages = getVillages(cursor)
    areas=getAreas(cursor)
    districts=getDistricts(cursor)
    for (rec,cs) in result.items():
        for c in cs:
            areaName=c[u'area'].encode("utf-8")
            districtName=c[u'distinct'].encode("utf-8")
            villageName=c[u'village'].encode("utf-8")
            area=0
            district=0
            village=0
            if villageName in villages.keys():
                village=int(villages[villageName])
            if areaName in areas.keys():
                area=int(areas[areaName])
            if districtName in districts.keys():
                district=int(districts[districtName])
            data_daily = {
                    "avgPrice": int(c['avgPrice']),
                    "in90": int(c['in90']),
                    "sailCount": int(c['sailCount']),
                    "viewCount": int(c['viewCount']),
                    "city": 1,
                    "village": village,
                    "area": area,
                    "district": district,
                    "rec_time": c[u'time'].encode("utf-8").replace("T", " ")[0:19]
            }
            cursor.execute(add_village_daily, data_daily)
            conn.commit()    
    
def dbToInflux():
    query = ("SELECT avgPrice,in90,sailCount,viewCount,agent,city,area,district,village,rec_time FROM village_inf")
    cursor.execute(query)
    
    houseTemplates=[]
    for (avgPrice,in90,sailCount,viewCount,agent,area,district,village,rec_time) in cursor:    
        houseTemplate={}
        houseTemplate["measurement"]="HouseSales"
        tags={}
        houseTemplate["tags"]  = tags
        fields = {}
    
        fields["agent"] = agent
        fields["city"] = 1
        fields["district"] = district
        fields["area"] = area
        fields["village"] = village       
        fields["avgPrice"] = avgPrice
        fields["sailCount"] = sailCount
        fields["in90"] = in90
        fields["viewCount"] = viewCount
        fields["time"] = rec_time.strftime('%Y-%m-%d %H:%M:%S')
        houseTemplate["fields"]  = fields
        
        houseTemplates.append(houseTemplate)
        if len(houseTemplates) == 10:
            client.write_points(houseTemplates)
            houseTemplates=[]
    if len(houseTemplates) > 0:
        client.write_points(houseTemplates)
    pass

def cityToInflux():
    query = ("SELECT id,name from city")
    cursor.execute(query)
    
    houseTemplates=[]
    for (cityid, name) in cursor:    
        houseTemplate={}
        houseTemplate["measurement"]="Cities"
        tags={}
        tags["sid"] = str(cityid) 
        tags["name"] = name        
        houseTemplate["tags"]  = tags
        fields = {}
        fields["id"] = str(cityid)
        houseTemplate["fields"]  = fields
        houseTemplates.append(houseTemplate)
        if len(houseTemplates) == 10:
            client.write_points(houseTemplates)
            houseTemplates=[]
    if len(houseTemplates) > 0:
        client.write_points(houseTemplates)
    pass

def districtToInflux():
    query = ("SELECT id,name,city_id from district")
    cursor.execute(query)
    
    houseTemplates=[]
    for (districtid, name,city_id) in cursor:    
        houseTemplate={}
        houseTemplate["measurement"]="Districts"
        tags={}
        tags["sid"] = str(districtid)
        tags["city_id"] = str(city_id)
        tags["name"] = name        
        houseTemplate["tags"]  = tags
        fields = {}
        fields["id"] = str(districtid)
        houseTemplate["fields"]  = fields
        houseTemplates.append(houseTemplate)
        if len(houseTemplates) == 10:
            client.write_points(houseTemplates)
            houseTemplates=[]
    if len(houseTemplates) > 0:
        client.write_points(houseTemplates)
    pass

def areaToInflux():
    query = ("SELECT id,name,district_id from area")
    cursor.execute(query)
    
    houseTemplates=[]
    for (areaid, name,district_id) in cursor:    
        houseTemplate={}
        houseTemplate["measurement"]="Areas"
        tags={}
        tags["sid"] = str(areaid)    
        tags["district_id"] = str(district_id)           
        tags["name"] = name        
        houseTemplate["tags"]  = tags
        fields = {}
        fields["id"] = str(areaid)    
        houseTemplate["fields"]  = fields
        houseTemplates.append(houseTemplate)
        if len(houseTemplates) == 10:
            client.write_points(houseTemplates)
            houseTemplates=[]
    if len(houseTemplates) > 0:
        client.write_points(houseTemplates)
    pass


def villageToInflux():
    query = ("SELECT id,name,area_id from village")
    cursor.execute(query)
    
    houseTemplates=[]
    for (villageId, name,area_id) in cursor:    
        houseTemplate={}
        houseTemplate["measurement"]="Villages"
        tags={}
        tags["name"] = name
        tags["sid"] = str(villageId)
        tags["area_id"] = str(area_id)        
        houseTemplate["tags"]  = tags
        fields = {}
        fields["id"] = str(villageId)
        houseTemplate["fields"]  = fields
        houseTemplates.append(houseTemplate)
        if len(houseTemplates) == 10:
            client.write_points(houseTemplates)
            houseTemplates=[]
    if len(houseTemplates) > 0:
        client.write_points(houseTemplates)
    pass

if __name__ == '__main__':
    hostname = socket.gethostname()    
    if hostname == "WAGAN":
        client = InfluxDBClient('127.0.0.1', 8086, '', '', 'RealEstate')
    else:
        client = InfluxDBClient('10.58.80.137', 8086, '', '', 'RealEstate')    
    if hostname == "WAGAN":
        conn = mysql.connector.connect(host='192.168.1.50', port = 13306,user='root',passwd='Initial0',db='realestate')
    else:
        conn = mysql.connector.connect(host='10.58.80.137', port = 3306,user='root',passwd='Initial0',db='realestate')
    cursor = conn.cursor()
    villageToInflux()
    
    #dailyId = getRecordDate(cursor)    
    #recordDaily(cursor, dailyId)
    #houses = getHouses(cursor)
    #for (code, id) in houses.items():
    #    url = "http://sh.lianjia.com/ershoufang/sh" + code +".html"
    #    parseHousePage(url, code, cursor)
    #cursor.close()
    #conn.close()
    pass