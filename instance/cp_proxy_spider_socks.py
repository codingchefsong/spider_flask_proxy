import time

import schedule
import urllib3
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# from flaskr.db import get_db
import sqlite3


def get_db():
    # debug
    # db = sqlite3.connect('flaskr.sqlite')
    db = sqlite3.connect('/root/flask_proxy/venv/var/flaskr-instance/flaskr.sqlite')
    return db


"""
    Spider
    爬虫每十分钟获取一次
"""

# 设置一个目标目录
tarpath = "/var/www/wordpress/"


def getip():
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(datetime, "Open browser get info...")
    # 获取ip和port，返回list
    # example: [192.168.0.0:8080]
    url = "http://spys.one/free-proxy-list/CN/"
    ip_port_dict = {}
    try:
        chromeoptions = Options()
        chromeoptions.add_argument("--headless")
        chromeoptions.add_argument("--no-sandbox")
        chromeoptions.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chromeoptions)
        driver.get(url)
        html = driver.page_source
        # print(html)
        soup = BeautifulSoup(html, features='lxml')
        tr = soup.find_all("tr", class_=["spy1x", "spy1xx"])
        ip_port_dict = {}
        for i in range(2, len(tr)):
            # print(i)
            # print(tr[i].font.get_text())
            ip = tr[i].font.get_text().split(":")[0]
            port = tr[i].font.get_text().split(":")[1]
            print(ip, port)
            # print(port)
            ip_port_dict[ip] = port
        driver.quit()
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(datetime, "Close browser.")

    except:
        # print(e)
        print("Requests Failed!")
        pass
    # save to database
    # db.add(ip_port_dict)
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
        created   TIMESTAMP NOT NULL
                            DEFAULT CURRENT_TIMESTAMP,
        ip        TEXT      NOT NULL,
        port      TEXT      NOT NULL,
        delay     TEXT,
        FOREIGN KEY (
            author_id
        )
        REFERENCES user (id));
        """)

    db.commit()

    for ip, port in ip_port_dict.items():
        # cursor.execute("REPLACE INTO PROXY (DATETIME, IP, PORT) VALUES (?,?,?)", (datetime, ip, port))
        db.execute("INSERT INTO proxy (created, ip, port, author_id) VALUES (?,?,?,?)", (datetime, ip, port, 1))
    db.commit()


def tryip():
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(datetime, "Test proxy ip...")

    # 测试目标url返回的延迟
    # 返回带有延迟的字典 '192.168.0.0:8080':0.01
    url = "http://music.163.com"
    # 从database获取所有ip
    # ip_port_dic = db.select_all()
    db = get_db()
    ip_port_dic = db.execute("SELECT id,ip,port from proxy ORDER BY created DESC").fetchall()
    # dict 存储测试过的id,delay
    delay_dict = {}

    send_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/61.0.3163.100 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8"}
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for i, ip, port in ip_port_dic:
        # print(i,ip,port)
        proxy_dict = {"http": "socks5://" + ip + ':' + port}
        try:
            s = requests.Session()
            a = requests.adapters.HTTPAdapter(max_retries=2)
            s.mount('http://', a)
            r = s.get(url, headers=send_headers, verify=False, proxies=proxy_dict, timeout=1.5)
            # 过滤不能返回的，留下成功返回的
            if r.status_code == 200:
                elapsed = r.elapsed.total_seconds()
                print("{:10.2f}".format(elapsed) + "\t" + ip + ':' + port)
                delay_dict[i] = str(elapsed)
                delay = str(elapsed)
                db.execute("UPDATE proxy set delay = ? WHERE ID = ?", (delay, i))
                db.commit()
        except requests.exceptions.RequestException as e:
            # print(e)
            pass
    # set the value to delay
    # db = get_db()
    # for i, delay in delay_dict.items():
    #     db.execute("UPDATE proxy set delay = ? WHERE ID = ?", (delay, i))
    # db.commit()


def updatefile(ip):
    n_line = "var proxy = \"SOCKS %s; DIRECT\";\n" % ip
    data = ""
    filepath = tarpath + "sample.pac"
    rfile = open(filepath, mode='r', encoding='utf-8')
    for line in rfile.readlines():
        if line.find("var proxy =") == 0:
            line = n_line
        data += line
    rfile.close()

    pacfile = open(filepath, mode='w+', encoding='utf-8')
    pacfile.writelines(data)
    pacfile.close()


def job():
    getip()
    tryip()
    db = get_db()
    try:
        record = db.execute(
            'SELECT ip, port, delay FROM proxy WHERE delay IS NOT NULL ORDER BY created DESC, delay ASC'
        ).fetchone()
        print('Proxy: %s:%s delay:%s' % (record[0], record[1], record[2]))
    except:
        pass

    # re = next(db.select_by_delay())
    # ip = re[2] + ':' + re[3]
    # print("Fastest proxy: " + '\t' + re[4] + '\t' + ip)
    # updatefile(ip)


job()
schedule.every(15).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
