# UnblockNeteaseMusic 
Spider crawl page get proxy ip and port, parse the ip and port, using web framework flask show the results.
- Using selenium, beautiful soup to get some proxy ip port from website save to datebase
- Using multithreading test every record ping music.163.com save the results to datebase
- Using falsk web framework and template to generate pac file.
# How to use
> host/proxy
- Generate the pac file.
> host/
- Shows all working proxy sorted by delay.
> host/dashboard
- Shows all records.
> host/pac0
- Pull out the fastest proxy record from database
> host/pac1
- Pull out the second fast record from database
> host/pac2
- etc.
> host/next
- The first record will be replaced by the second record. In case the first record is not working.


# How to depolyment

- (Debian Server) Set up a new virtualenv
```
$ mkdir flask_proxy
$ cd flask_proxy
$ apt install virtualenv python3-virtualenv
$ python3 -m venv venv
$ . venv/bin/activate
```
- Copy this file "dist/flaskr-1.0.0-py3-none-any.whl." to flask_proxy floder
```
$ pip install flaskr-1.0.0-py3-none-any.whl
$ export FLASK_APP=flaskr
$ flask init-db
```
- (Local machine) generate the Secret Key 
```
run gen_random_key.py
```
- Copy the string(example)"b'_5#y2L"F4Q8z\n\xec]/'"
- (Debian Server) config key
```
$ nano venv/var/flaskr-instance/config.py
```
- Paste SECRET_KEY = (example)b'_5#y2L"F4Q8z\n\xec]/' into the file
- (Debian Server) install and start WSGI server
```
$ pip install waitress
$ nohup waitress-serve --call 'flaskr:create_app' &
```
- start craw proxy ip
```
$ nohup python venv/var/flaskr-instance/proxy_spider_socks.py &
```
