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
    elif sysstr == "Windows":
        db = sqlite3.connect('instance/flaskr.sqlite')
    return db


def init_proxy_table():
    db = get_db()
    try:
        db.execute("DROP TABLE proxy")
    except:
        pass
    db.executescript("""
            CREATE TABLE proxy (
            id        INTEGER   PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER   NOT NULL,
            created   TIMESTAMP NOT NULL,
            updated   TIMESTAMP NOT NULL
                                DEFAULT CURRENT_TIMESTAMP,
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
    Every one hour get info
"""


def get_proxy_ip():
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print()
    print(datetime, "Open browser get info...")
    url = "http://spys.one/free-proxy-list/CN/"

    chromeoptions = Options()
    chromeoptions.add_argument("--headless")
    chromeoptions.add_argument("--no-sandbox")
    chromeoptions.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chromeoptions)

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
        ip_port_dict = {}
        for i in range(2, len(tr)):
            # print(tr[i].font.get_text())
            r = tr[i].font.get_text()
            ip = r.split(":")[0]
            port = r.split(":")[1]
            # print(ip, port)
            ip_port_dict[ip] = port
        # save to database
        print('Save to database...')
        db = get_db()
        for ip, port in ip_port_dict.items():
            # cursor.execute("REPLACE INTO PROXY (DATETIME, IP, PORT) VALUES (?,?,?)", (datetime, ip, port))
            db.execute("REPLACE INTO proxy (created, ip, port, author_id) VALUES (?,?,?,?)",
                       (datetime, ip, port, 1))
        db.commit()
    except:
        print('Fail to get info...')
        pass
    finally:
        driver.quit()
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(datetime, "Close browser.")


if __name__ == '__main__':
    get_proxy_ip()
    schedule.every(1).hours.do(get_proxy_ip)
    while True:
        schedule.run_pending()
        time.sleep(1)
