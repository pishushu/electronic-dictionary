'''
name :  Tedu
modules: pymysql
This is a dict project for AID
'''

from socket import *
import os 
import time
import signal 
import pymysql
import sys
from threading import Thread

#定义需要的全局变量
DICT_TEXT = './dict.txt'
HOST = '0.0.0.0'
PORT = 8000
ADDR = (HOST,PORT)

#处理僵尸进程
def zombie():
    os.wait()

#网络搭建，流程控制
def main():
    #创建数据库连接
    db = pymysql.connect('localhost','root','123456','cidian',charset='utf8')

    #创建套接字
    s = socket()
    s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    s.bind(ADDR)
    s.listen(5)

    while True:
        try:
            c,addr = s.accept()
            print('Connect from',addr)
        except KeyboardInterrupt:
            c.close()
            sys.exit('服务器退出')
        except Exception as e:
            print(e)
            continue

        #创建子进程
        pid = os.fork()
        if pid == 0:
            s.close()
            do_chile(c,db) #子进程函数   
        else:
            c.close()
            t = Thread(target=zombie)
            t.setDaemon(True)
            t.start()   
            continue

#出来客户端请求
def do_chile(c,db):
    while True:
        #接收客户端请求
        data = c.recv(128).decode() 
        #打印客户端的ＩＰ地址
        print(c.getpeername(),':',data)
        #判断接收的信息
        if (not data) or data[0] == 'E':  # 如果客户端ctrl+c退出(not data)
            print('进程退出')
            c.close()
            sys.exit()
        elif data[0] == 'R':
            do_register(c,db,data)
        elif data[0] == 'L':
            do_login(c,db,data)
        elif data[0] == 'Q':
            do_query(c,db,data)
        elif data[0] == 'H':
            do_hist(c,db,data)

#注册用户
def do_register(c,db,data):
    l = data.split(' ')
    name = l[1]
    passwd = l[2]
    cur = db.cursor()

    sql = "select * from user where user_name = '%s'"%name
    cur.execute(sql)
    r = cur.fetchone()

    if r != None:
        c.send(b'EXISTS')
        return
    #插入用户
    sql = "insert into user (user_name,password) values('%s','%s')"%(name,passwd)
    try:
        cur.execute(sql)
        db.commit()
        c.send(b'OK')
    except:
        db.rollback()
        c.send(b'FALL')

#登录用户
def do_login(c,db,data):
    l = data.split(' ')
    name = l[1]
    passwd = l[2]
    cur = db.cursor()

    sql = "select * from user where user_name = '%s'"%name
    cur.execute(sql)
    r = cur.fetchone()

    if r == None:
        c.send(b'user')
        return

    sql = "select password from user where user_name = '%s'"%name
    cur.execute(sql)
    p = cur.fetchone() 

    if p[0] != passwd:
        c.send(b'passwd')
        return
    elif p[0] == passwd:
        c.send(b'OK')

def do_query(c,db,data):
    l = data.split(' ')
    name = l[1]
    word = l[2]
    cursor = db.cursor()

    def insert_history():
        tm = time.ctime()
        sql="insert into hist (name,word,time) \
        values ('%s','%s','%s')"%(name,word,tm)
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()

    #使用单词本查找
    try:
        f = open(DICT_TEXT)
    except:
        c.send(b"FALL")
        return 
    for line in f:
        tmp = line.split(' ')[0]
        if tmp > word:
            c.send(b"FALL")
            f.close()
            return
        if tmp == word:
            c.send(line.encode())
            f.close()
            insert_history()
            return 
    c.send(b'FALL')
    f.close()



#查看历史记录
def do_hist(c,db,data):
    l = data.split(' ')
    name = l[1]
    cur = db.cursor()
    sql = "select * from hist where name = '%s'"%name
    cur.execute(sql)
    r = cur.fetchall()
    if not r:
        c.send(b'fall')
        return
    else:
        c.send(b'OK')
        time.sleep(0.1)
    for i in r:
        msg = "%s   %s   %s"%(i[1],i[2],i[2])
        c.send(msg.encode())
        time.sleep(0.1)
    c.send(b'##')



if __name__ == '__main__':
    main()