# -*- coding: utf-8 -*-
# author:liucong


import importlib
import sys

import pymysql
import pymysql.cursors

from tools.log import logger

importlib.reload(sys)

# 海马聊天/商城
qywl = dict(host='11.0.21.17', user='platform', passwd='platform2018', port=23306, db='qywl', charset='utf8',
            cursorclass=pymysql.cursors.DictCursor)
# 企业通讯录/日志/客户管理
enterprise = dict(host='11.0.21.17', user='platform', passwd='platform2018', port=23306, db='enterprise',
                  charset='utf8', cursorclass=pymysql.cursors.DictCursor)
# 轻易贷
qyd = dict(host='11.0.21.17', user='platform', passwd='platform2018', port=23306, db='qydproduction', charset='utf8',
           cursorclass=pymysql.cursors.DictCursor)


class mysqldb(object):
    def __init__(self, dbName):

        if dbName == "qywl":
            self.conn = qywl
        elif dbName == "enterprise":
            self.conn = enterprise
        elif dbName == "qyd":
            self.conn = qyd
        else:
            pass

    def selectsql(self, sql):
        con = pymysql.connect(**self.conn)
        cursor = con.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        con.close()
        return data

    def updatesql(self, sql):
        conn = pymysql.connect(**self.conn)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        try:
            cursor.execute(sql)
            # logger.info(sql)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(e.message)

    def insertsql(self, sql):
        conn = pymysql.connect(**self.conn)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()

# if __name__ == '__main__':
#

# sql_1 = "select user_id from loan_user_credit_line where sso_id= %s limit 1"
# params_1 = "1115747561558587297"
# sqlresult_1 = mysqldb("qydnewproduction").selectsql(sql_1 % params_1)
# params_2 = "30e66a5a-e53c-416b-bcf5-3446dded05f3"
# sql_2 = 'select repay_date FROM loan_loan WHERE borrower_id="' + str(params_2) + '" ORDER BY repay_date ASC'

# print("查询1结果：" + str(sqlresult_1) + "取参结果：" + params_2)
# print("bb659559")
# sqlresult_2 = mysqldb("qydnewproduction").selectsql(sql_2)
# firsttime = sqlresult_2[0]['repay_date']
# print("第二个查询结果："+str(firsttime))
# abc = (1,2,3)
# if type(abc) == tuple:
#     print("hhahhah")
# print(type(abc))
# querysql='SELECT * from mallLogistics a where a.id=\'01d22ee7-bb36-439c-b9fb-1ae1776f20d0\';'
# sqlres=mysqldb("qywl").selectsql(querysql)
# print(
#     sqlres
# )
# print(sqlres[0]['homePositionId'])
# """以上三种方法足以进行mysql的查询和更新操作---最新框架"""

# selectuid = "SELECT id FROM qywl.users WHERE phone = '16810061988';"
# userId = mysqldb("qywl").selectsql(selectuid)[0].get("id")
# print(userId)
# selectcompany = "select companyId from enterprise.employee where userId ='%s'" % userId
# company = mysqldb("enterprise").selectsql(selectcompany)[0].get("companyId")
# print(company)
# selectdepartment = "select id from enterprise.department where companyId='{company}'".format(company=company)
# departmentId = mysqldb("enterprise").selectsql(selectdepartment)
# print(departmentId)
# departmentIds=[]
# for i in range(len(departmentId)):
#     departmentIds.append(departmentId[i].get("id"))
# print(departmentIds)

