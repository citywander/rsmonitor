'''
Created on Mar 29, 2017

@author: I076054
'''
import xlrd
import socket
import mysql.connector

add_school = ("INSERT INTO school "
              "(name)"
              "VALUES (%(name)s)")

update_e_school = ("UPDATE village "
              "set e_school_id=%(e_school_id)s"
              " where id=%(id)s")

update_m_school = ("UPDATE village "
              "set m_school_id=%(m_school_id)s"
              " where id=%(id)s")

class SchoolHouse:
    
    def __init__(self, id, address):
        self.id = id
        self.address = address
        pass
    
    def __str__(self):
        return self.address + "(" + str(self.id) + ")"
        
    pass

def addSchools(cursor):
    data = xlrd.open_workbook('C:/etc/mschool.xls')
    table = data.sheets()[0]
    schools = set()
    for i in range(1, table.nrows):
        schools.add(table.row_values(i)[3].encode("utf-8"))
        pass  
    for name in schools:
        data_school = {
            'name': name
        }
        cursor.execute(add_school, data_school)
    conn.commit()      
    pass

def getSchoolsFromExcel(cursor, level):
    if level == 1:
        data = xlrd.open_workbook('C:/etc/school.xls')
    else:
        data = xlrd.open_workbook('C:/etc/mschool.xls')
    table = data.sheets()[0]
    schoolHouses = []
    schools=getSchools(cursor, level)
    for i in range(1, table.nrows):
        name = table.row_values(i)[3].encode("utf-8")
        address = table.row_values(i)[5].encode("utf-8")
        if name in schools:
            id=schools[name]
            schoolHouses.append(SchoolHouse(id, address))
        pass
    print schoolHouses
    return schoolHouses
  
def getSchools(cursor, level):
    query = ("SELECT id, name FROM school where level=" + str(level))
    cursor.execute(query)
    schools = {}
    for (id, name) in cursor:
        schools[name.encode("utf-8")]=id
    return schools    

def getVillages(cursor, level):
    if level == 1:
        query = ("SELECT id, address from village")
    else:
        query = ("SELECT id, address from village")
    cursor.execute(query)
    villages = {}
    for (id, address) in cursor:
        villages[id]=address.encode("utf-8")
    return villages  

def updateDistinct(cursor,level):
    villages=getVillages(cursor,level)
    sh=getSchoolsFromExcel(cursor,level)
    for (id, addresses) in villages.items():
        for address in addresses.split(","):
            for oi in sh:
                if address in oi.address:
                    if level == 1:
                        data_school = {
                            'id': id,
                            'e_school_id': oi.id
                        }
                        cursor.execute(update_e_school, data_school)
                    else:
                        data_school = {
                            'id': id,
                            'm_school_id': oi.id
                        }
                        print update_m_school
                        cursor.execute(update_m_school, data_school)                        
                   
                    conn.commit()
                    break
    pass

if __name__ == '__main__':

    hostname = socket.gethostname()
    if hostname == "WAGAN":
        conn = mysql.connector.connect(host='192.168.1.50', port = 13306,user='root',passwd='Initial0',db='realestate')
    else:
        conn = mysql.connector.connect(host='10.58.81.211', port = 3306,user='root',passwd='Initial0',db='realestate')
    cursor = conn.cursor()
    #updateDistinct(cursor,1)
    updateDistinct(cursor,2)
    #addSchools(cursor)
    pass