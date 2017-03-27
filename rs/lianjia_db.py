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

access_token="7poanTTBCymmgE0FOn1oKp"

add_district = ("INSERT INTO district "
              "(city_id, code, name)"
              "VALUES (%(city_id)s, %(code)s, %(name)s)")

add_area = ("INSERT INTO area "
              "(district_id, code, name)"
              "VALUES (%(district_id)s, %(code)s, %(name)s)")

add_village = ("INSERT INTO village "
              "(area_id, code, name)"
              "VALUES (%(area_id)s, %(code)s, %(name)s)")

update_detail_village = ("UPDATE village "
              "set complete_year=%(complete_year)s, cycle_line=%(cycle_line)s, dev_company=%(dev_company)s, property_type=%(property_type)s, mgt_company=%(mgt_company)s, web_url=%(web_url)s, building_count=%(buiding_count)s, property_count=%(property_count)s,address=%(address)s"
              " where code=%(code)s")

add_house = ("INSERT INTO house "
              "(village_id, code, title, face, floor_state, is_five, is_new, room, hall, price, login_date, acreage)"
              "VALUES (%(village_id)s, %(code)s, %(title)s, %(face)s, %(floor_state)s, %(is_five)s, %(is_new)s, %(room)s, %(hall)s, %(price)s, %(login_date)s, %(acreage)s)")

update_house = ("UPDATE house "
              "set saled_date=%(saled_date)s"
              " where code=%(code)s")


def load():
    f = open('cities.yml')
    x = yaml.load(f)
    return x  

settings= load()

def parseMap(city, dateId, siteType, type):    
    url="http://soa.dooioo.com/api/v4/online/house/ershoufang/listMapResult?access_token=%s&cityCode=%s&siteType=%s&type=%s&dataId=%s"
    url = url % (access_token, city, siteType, type, dateId)
    page = urllib2.urlopen(url)
    return json.load(page)["dataList"]
    
def insertDistrict(cursor):
    districts = parseMap("sh", "sh", "quyu", "district")
    for district in districts:
        data_district = {
          'city_id': 1,
          'code': district["dataId"],
          'name': district["showName"]
        }
        cursor.execute(add_district, data_district)

def getDistrict(cursor):
    districts={}
    query = ("SELECT id, code FROM district")
    cursor.execute(query)
    for (id, code) in cursor:
        districts[code]=id
    return districts

def getAreas(cursor):
    areas={}
    query = ("SELECT id, code FROM area")
    cursor.execute(query)
    for (id, code) in cursor:
        areas[code]=id
    return areas    

def insertArea(districts_dict):
    for (k,v) in districts_dict.items():
        areas = parseMap("sh", k, "quyu", "plate")
        for area in areas:
            data_area = {
              'district_id': v,
              'code': area["dataId"],
              'name': area["showName"]
            }
            cursor.execute(add_area, data_area)
    pass

def insertVillage(areas_dict):
    for (k,v) in areas_dict.items():
        areas = parseMap("sh", k, "quyu", "village")
        for area in areas:
            data_village = {
              'area_id': v,
              'code': area["dataId"],
              'name': area["showName"]
            }
            cursor.execute(add_village, data_village)
    pass

def getVillages(cursor, isnull=True):
    villages={}
    if isnull:
        query = ("SELECT id, code FROM village where web_url IS NULL ")
    else:
        query = ("SELECT id, code FROM village")
    cursor.execute(query)
    for (id, code) in cursor:
        villages[code]=id
    return villages 

def updateDetailVillage(conn, cursor):
    villages=getVillages(cursor)
    for (k,v) in villages.items():
        url="http://soa.dooioo.com/api/v4/online/house/ershoufang/search?access_token=%s&cityCode=sh&community_id=%s&limit_offset=1&limit_count=500"
        url = url % (access_token, k)
        page = urllib2.urlopen(url)
        prop = json.load(page)["data"]["prop"]
        print prop["propertyAddress"]
        if not "devCompany" in prop:
            prop["devCompany"] = ""
        if not "mgtCompany" in prop:
            prop["mgtCompany"] = ""
        if not "completeYear" in prop:
            prop["completeYear"] = ""            
        if not "cycleLine" in prop:
            prop["cycleLine"] = "" 
        data_village = {
          'code': k,
          'complete_year': prop["completeYear"],
          'cycle_line': prop["cycleLine"],
          'dev_company': prop["devCompany"],
          'property_type': prop["houseType2"],
          'mgt_company': prop["mgtCompany"],
          'web_url': prop["webUrl"],
          'buiding_count': prop["buildingCount"],
          'property_count': prop["totalRooms"],
          'address': prop["propertyAddress"]
        }
        cursor.execute(update_detail_village, data_village)   
        conn.commit()
        
def getHouses(cursor):
    houses={}
    query = ("SELECT code,saled_date FROM house")
    cursor.execute(query)
    for (code,saled_date) in cursor:
        houses[code] = not saled_date is None
    return houses     

def insertHouse(conn, cursor):
    villages=getVillages(cursor, False)
    houseCodes = getHouses(cursor)
    now = datetime.datetime.now()
    for (k,v) in villages.items():
        url="http://soa.dooioo.com/api/v4/online/house/ershoufang/search?access_token=%s&cityCode=sh&community_id=%s&limit_offset=1&limit_count=1000"
        url = url % (access_token, k)
        page = urllib2.urlopen(url)
        properties = json.load(page)["data"]["list"]
        for prop in properties:
            code = prop["houseSellId"]
            tags = prop["tags"]
            if "face" not in prop:
                prop["face"] = ""
            data_house = {
              'village_id': v,
              'code': code,
              'title': prop["title"],
              'face': prop["face"],
              'floor_state': prop["floor_state"],
              'is_five': "is_five_year" in tags,
              'is_new': "is_new_house_source" in tags,
              'room': prop["room"],
              'hall': prop["hall"],
              'price': prop["showPrice"],
              'login_date': now.strftime('%Y-%m-%d %H:%M:%S'),
              'acreage': prop["acreage"]
            }
            if not code in houseCodes:
                cursor.execute(add_house, data_house)
            else:
                del houseCodes[code]
        conn.commit()
    for (code,isSaled) in houseCodes.items():
        if isSaled:
            continue
        update_house_data = {
            'code': code,
            'saled_date': now.strftime('%Y-%m-%d %H:%M:%S')
        }
        cursor.execute(update_house, update_house_data)     
        pass 
    conn.commit()


if __name__ == '__main__':
    hostname = socket.gethostname()
    if hostname == "WAGAN":
        conn = mysql.connector.connect(host='192.168.1.50', port = 13306,user='root',passwd='Initial0',db='realestate')
    else:
        conn = mysql.connector.connect(host='10.58.81.211', port = 3306,user='root',passwd='Initial0',db='realestate')
    cursor = conn.cursor()
    insertHouse(conn, cursor)
    conn.commit()
    cursor.close()
    conn.close()
    pass