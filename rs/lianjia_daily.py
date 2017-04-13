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
import Queue
import ljutils

add_daily = ("INSERT INTO daily "
              "(rec_date)"
              "VALUES (%(rec_date)s)")

add_village_daily = ("INSERT INTO village_daily "
              "(avgPrice, in90, sailCount, viewCount, village_id, daily_id)"
              "VALUES (%(avgPrice)s, %(in90)s, %(sailCount)s,%(viewCount)s,%(village_id)s, %(daily_id)s)")

q=Queue.Queue(2) 

maxProducer=2

def getVillages(cursor):
    villages={}
    query = ("SELECT id, code FROM village")
    cursor.execute(query)
    for (id, code) in cursor:
        villages[code]=id
    return villages

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
    print url
    #cursor.execute(add_village_daily, data_daily)
    #conn.commit()   
    #return soup

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
        (_, avgPrice, in90, sailCount, viewCount)=ljutils.parsePage(baseUrl)
        data_daily = {
            "avgPrice": avgPrice,
            "in90": in90,
            "sailCount": sailCount,
            "viewCount": viewCount,
            "village_id": villageId,
            "daily_id": dailyId
        } 
        cursor.execute(add_village_daily, data_daily)
        conn.commit()        
    pass

def getHouses(cursor):
    houses={}
    query = ("SELECT id, code FROM house where is_checked=0 and saled_date is null")
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
    now = datetime.datetime.now()
    data_date = {
      'saled_date': now.strftime('%Y-%m-%d %H:%M:%S')
    }    
    if len(xiajia) > 0 or len(yishixiao)>0:
        updateSql=("update realestate.house set saled_date=%(saled_date)s,is_checked=1 where code='" + code + "'")
        cursor.execute(updateSql, data_date)        
    else:
        #updateSql="update realestate.house set saled_date=null,is_checked=1 where code='" + code + "'"
        #print code
        pass
    
    conn.commit()    

if __name__ == '__main__':
    hostname = socket.gethostname()
    if hostname == "WAGAN":
        conn = mysql.connector.connect(host='192.168.1.50', port = 13306,user='root',passwd='Initial0',db='realestate')
    else:
        conn = mysql.connector.connect(host='10.58.80.214', port = 3306,user='root',passwd='Initial0',db='realestate')
    cursor = conn.cursor()
    dailyId = getRecordDate(cursor)    
    recordDaily(cursor, dailyId)
    #houses = getHouses(cursor)
    #for (code, id) in houses.items():
    #    url = "http://sh.lianjia.com/ershoufang/sh" + code +".html"
    #    parseHousePage(url, code, cursor)
    cursor.close()
    conn.close()

    pass