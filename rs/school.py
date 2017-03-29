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

class SchoolHouse:
    
    def __init__(self, name, id):
        self.name = name
        self.id = id
        pass
    
    def SetAddress(self, address):
        self.address = address
    
    def __str__(self):
        return self.name + "(" + id + ")"
        
    pass

def addSchools(cursor):
    data = xlrd.open_workbook('C:/etc/school.xls')
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

def getSchools(cursor):
    query = ("SELECT id, name FROM district")
    cursor.execute(query)
    schools = {}
    for (id, name) in cursor:
        schools[name]=SchoolHouse(id=id, name=name)
    return schools    

if __name__ == '__main__':

    hostname = socket.gethostname()
    if hostname == "WAGAN":
        conn = mysql.connector.connect(host='192.168.1.50', port = 13306,user='root',passwd='Initial0',db='realestate')
    else:
        conn = mysql.connector.connect(host='10.58.81.211', port = 3306,user='root',passwd='Initial0',db='realestate')
    cursor = conn.cursor()
    #addSchools(cursor)
    pass