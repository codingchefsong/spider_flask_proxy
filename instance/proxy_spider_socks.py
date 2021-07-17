import time
import platform

import schedule
import urllib3
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# from flaskr.db import get_db
import sqlite3


def get_db():
    sysstr = platform.system()
    if sysstr == "Linux":
        db = sqlite3.connect('/root/flask_proxy/venv/var/flaskr-instance/flaskr.sqlite')
    # debug
    elif sysstr == "Windows":
        db = sqlite3.connect('flaskr.sqlite')
    return db


def init_proxy_table():
    db = get_db()
    # 清空表
    try:
        db.execute("DROP TABLE proxy")
    except:
        pass
    db.executescript("""
            CREATE TABLE proxy (
            id        INTEGER   PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER   NOT NULL,
            created   TIMESTAMP,
            updated   TIMESTAMP,
            delay     TEXT,
            ip        TEXT      NOT NULL
                                UNIQUE,
            port      TEXT      NOT NULL,
            FOREIGN KEY (
                author_id
            )
            REFERENCES user (id));
            """)
    db.commit()


def init_socks_table():
    db = get_db()

    # 清空表
    try:
        db.execute("DROP TABLE socks")
    except:
        pass
    db.executescript("""
        CREATE TABLE socks (
        id        INTEGER   PRIMARY KEY AUTOINCREMENT,
        
        updated   TIMESTAMP NOT NULL
                            DEFAULT CURRENT_TIMESTAMP,
        delay     TEXT,                            
        ip        TEXT      NOT NULL
                            UNIQUE,
        port      TEXT      NOT NULL,        
        author_id INTEGER   NOT NULL,
        FOREIGN KEY (
            author_id
        )
        REFERENCES user (id));
        """)

    db.commit()


"""
    Spider
    爬虫每一小时获取一次
"""


def get_proxy_ip():
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # print()
    print(datetime, "Open browser get info...")
    url = "http://spys.one/free-proxy-list/CN/"

    chromeoptions = Options()
    chromeoptions.add_argument("--headless")
    chromeoptions.add_argument("--no-sandbox")
    chromeoptions.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chromeoptions)

    ip_port_dict = {}
    try:
        driver.get(url)
        # html = driver.page_source
        # print(html)

        # select socks
        time.sleep(3)
        xf5 = Select(driver.find_element_by_id('xf5'))
        xf5.select_by_visible_text('SOCKS')

        time.sleep(3)
        xf5 = Select(driver.find_element_by_id('xf5'))
        xf5.select_by_visible_text('SOCKS')

        time.sleep(3)
        html = driver.page_source
        # print(html)
        soup = BeautifulSoup(html, features='lxml')
        tr = soup.find_all("tr", class_=["spy1x", "spy1xx"])

        for i in range(2, len(tr)):
            # print(tr[i].font.get_text())
            r = tr[i].font.get_text()
            ip = r.split(":")[0]
            port = r.split(":")[1]
            # print(ip, port)
            ip_port_dict[ip] = port

    except:
        print('Fail to get info...')
        pass
    finally:
        driver.quit()
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(datetime, "Close browser.")

    # save to database
    db = get_db()
    for ip, port in ip_port_dict.items():
        # cursor.execute("REPLACE INTO PROXY (DATETIME, IP, PORT) VALUES (?,?,?)", (datetime, ip, port))
        db.execute("REPLACE INTO proxy (created, ip, port, author_id) VALUES (?,?,?,?)",
                   (datetime, ip, port, 1))
    db.commit()
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # print(datetime, "Save to database...")


# def test_proxy_ip():
#     datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#     print()
#     print(datetime, "Test proxy ip...")
#
#     # 测试目标url返回的延迟
#     url = "http://music.163.com"
#     # 从database获取所有ip
#     # ip_port_dic = db.select_all()
#     db = get_db()
#     # ip_port_dic = db.execute("SELECT id,ip,port from proxy ORDER BY created DESC").fetchall()
#     ip_port_dic = db.execute("SELECT id,ip,port FROM proxy WHERE created =(SELECT MAX(created) FROM proxy)").fetchall()
#     # dict 存储测试过的id,delay
#     delay_dict = []
#
#     send_headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
#                       "Chrome/61.0.3163.100 Safari/537.36",
#         "Connection": "keep-alive",
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#         "Accept-Language": "zh-CN,zh;q=0.8"}
#     urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#     t_start = time.time()
#     for i, ip, port in ip_port_dic:
#         # 计时器
#         time_start = time.time()
#         # print(i,ip,port)
#         proxy_dict = {"http": "socks5://" + ip + ':' + port}
#         try:
#             s = requests.Session()
#             a = requests.adapters.HTTPAdapter(max_retries=1)
#             s.mount('http://', a)
#             r = s.get(url, headers=send_headers, verify=False, proxies=proxy_dict, timeout=(3.05, 3.05))
#             # 过滤不能返回的，留下成功返回的
#             # print(r.status_code)
#             if r.status_code == 200:
#                 elapsed = r.elapsed.total_seconds()
#                 print("{:10.2f}".format(elapsed) + "\t" + ip + ':' + port)
#                 delay = str(elapsed)
#
#                 delay_dict.append((ip, port, delay))
#                 db.execute("INSERT INTO socks (updated, ip, port, delay, author_id) VALUES (?,?,?,?,?)",
#                            (datetime, ip, port, delay, 1))
#                 # db.execute("INSERT into socks set delay = ?, updated = ? WHERE ID = ?", (delay, datetime, i))
#                 db.commit()
#         except requests.exceptions.ReadTimeout:
#             pass
#         except requests.exceptions.ConnectTimeout:
#             pass
#         except requests.exceptions.ConnectionError:
#             pass
#         except requests.exceptions.RequestException as e:
#             print(e)
#             pass
#         time_end = time.time()
#         # print('time cost: ', time_end - time_start, 's')
#     t_end = time.time()
#     print('Total time cost: ', t_end - t_start, 's')


if __name__ == '__main__':

    # init db
    # init_proxy_table()
    # init_socks_table()

    get_proxy_ip()
    schedule.every(1).hours.do(get_proxy_ip)

    while True:
        schedule.run_pending()
        time.sleep(1)
