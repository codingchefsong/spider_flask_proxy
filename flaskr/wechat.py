from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)

from flask import request
import hashlib
import xml.etree.ElementTree as ET
from flask import make_response
import time

bp = Blueprint('wechat', __name__)


@bp.route('/wechat', methods=["GET", "POST"])
def wechat():
    if request.method == "GET":
        data = request.args
        signature = data.get('signature')
        timestamp = data.get('timestamp')
        nonce = data.get('nonce')
        echostr = data.get('echostr')
        print(signature)

        # 自己的token
        token = "tokenchicago"  # 这里改写你在微信公众平台里输入的token
        # 字典序排序
        data = sorted([token, timestamp, nonce])  # 字典排序
        string = ''.join(data).encode('utf-8')  # 拼接成字符串
        hashcode = hashlib.sha1(string).hexdigest()  # sha1加密

        print(hashcode)
        if hashcode == signature:
            return echostr
        else:
            return ""
    if request.method == "POST":

        xml = ET.fromstring(request.data)
        toUser = xml.find('ToUserName').text
        fromUser = xml.find('FromUserName').text
        msgType = xml.find("MsgType").text

        if msgType == 'text':
            content = xml.find('Content').text
            return reply_text(fromUser, toUser, content)


def reply_text(to_user, from_user, content):
    reply = """
    <xml><ToUserName><![CDATA[%s]]></ToUserName>
    <FromUserName><![CDATA[%s]]></FromUserName>
    <CreateTime>%s</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[%s]]></Content>
    <FuncFlag>0</FuncFlag></xml>
    """
    response = make_response(reply % (to_user, from_user, str(int(time.time())), content))
    response.content_type = 'application/xml'
    return response
