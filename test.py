# -*- coding: utf-8 -*-
# Loading Google App Engine Libraries
import sys
from time import sleep

import webapp2
from google.appengine.api import urlfetch
from google.appengine.ext import ndb

reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.insert(0, 'libs')

# Loading Libraries about URL, JSON, LOG, Regular Expression
import urllib
import urllib2
import json
import logging
import re
from bs4 import BeautifulSoup
import mechanize
import mechanize._response

# Bot Token and Bot API URL
TOKEN = '324210401:AAEn368XSdzx6egfvIxZsuMXguJ3HbDYMU0'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

# Command to response by Bot
CMD_START     = '/start'
CMD_STOP      = '/stop'
CMD_HELP      = '/help'
CMD_BROADCAST = '/broadcast'
CMD_SHOP      = '/shop'
CMD_GETSHOP   = '/getshop'
CMD_SEARCH    = '/search'

# Help Messages & Response Messages
USAGE = u"""알라딘 중고서적 검색 봇 사용법
/start   - 봇 시작하기
/stop    - 봇 중단하기
/shop    - 특정 매장 설정하기
/getshop - 설정된 매장 보기
/help    - 도움말 보기
"""

MSG_START = u'Start Bot.'
MSG_STOP  = u'Stop Bot.'
MSG_SHOP  = u'현재 지정된 매장은 '

ALADIN_URL = 'http://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=UsedStore&'

# Custom keyboard
START_KEYBOARD = [
        [CMD_START],
        [CMD_HELP],
        ]

SEARCH_KEYBOARD = [
        [CMD_SHOP],
        [CMD_GETSHOP],
        [CMD_STOP],
        [CMD_HELP],
        ]

SHOP_KEYBOARD = [
        [u'/shop 전체'],
        [u'/shop 강남점'],
        [u'/shop 건대점'],
        [u'/shop 광주점'],
        [u'/shop 노원점'],
        [u'/shop 대구동성로점'],
        [u'/shop 대구상인점'],
        [u'/shop 대전시청역점'],
        [u'/shop 대전은행점'],
        [u'/shop 대학로점'],
        [u'/shop 부산경성대, 부경대역점'],
        [u'/shop 부산서면점'],
        [u'/shop 부산센텀점'],
        [u'/shop 부천점'],
        [u'/shop 북수원홈플러스점'],
        [u'/shop 분당서현점'],
        [u'/shop 분당야탑점'],
        [u'/shop 산본점'],
        [u'/shop 수원점'],
        [u'/shop 수유점'],
        [u'/shop 신림점'],
        [u'/shop 신촌점'],
        [u'/shop 연신내점'],
        [u'/shop 울산점'],
        [u'/shop 인천계산홈플러스점'],
        [u'/shop 일산점'],
        [u'/shop 잠실롯데타워점'],
        [u'/shop 잠실신천점'],
        [u'/shop 전주점'],
        [u'/shop 종로점'],
        [u'/shop 천안점'],
        [u'/shop 청주점'],
        [u'/shop 합정점']
        ]

class EnableStatus(ndb.Model):
    enabled = ndb.BooleanProperty(required=True, indexed=True, default=False,)
    shop_id = ndb.StringProperty(default=u'All',)

def set_enabled(chat_id, enabled):
    u"""set_enabled: Change Bot Status
    chat_id:    (integer) Chating ID to Status of Bot
    enabled:    (boolean) Flag about Bot Status
    """
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = enabled
    es.put()

def get_enabled(chat_id):
    u"""get_enabled: Return Bot Status
    return: (boolean)
    """
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def set_shop(chat_id, shop_id):
    es = EnableStatus.get_by_id(str(chat_id))
    es.shop_id = shop_id
    es.put()

def get_shop(chat_id):
    # es = EnableStatus.get_by_id(str(chat_id))
    # if es:
    #     return es.shop_id
    return u'All'

def get_enabled_chats():
    u"""get_enabled: Return Chatting List to enable Bot
    return: (list of EnableStatus)
    """
    query = EnableStatus.query(EnableStatus.enabled == True)
    return query.fetch()

def send_msg(chat_id, text, reply_to=None, no_preview=True, keyboard=None):
    u"""send_msg: Sending Messages
    chat_id:    (integer) Chat ID
    text:       (string)  Contents of Message
    reply_to:   (integer) Reply about Message
    no_preview: (boolean) Disable to Preview of URL Auto Link
    keyboard:   (list)    Set Custom Keyboard
    """
    params = {
        'chat_id': str(chat_id),
        'text': text.encode('utf-8'),
        'parse_mode': 'markdown'
        }
    if reply_to:
        params['reply_to_message_id'] = reply_to
    if no_preview:
        params['disable_web_page_preview'] = no_preview
    if keyboard:
        reply_markup = json.dumps({
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': False,
            'selective': (reply_to != None),
            })
        params['reply_markup'] = reply_markup
    try:
        print(keyword)
        print(len(text))
        print(unicode(len(text)))
        if len(text) < 5000:
            print(text)
        # print(text)
        # urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode(params)).read()
    except Exception as e:
        print(e.message)
        logging.exception(e)

def broadcast(text):
    for chat in get_enabled_chats():
        send_msg(chat.key.string_id(), text)

def cmd_start(chat_id):
    set_enabled(chat_id, True)
    send_msg(chat_id, MSG_START, keyboard=SEARCH_KEYBOARD)

def cmd_stop(chat_id):
    set_enabled(chat_id, False)
    set_shop(chat_id, u'All')
    send_msg(chat_id, MSG_STOP, keyboard=START_KEYBOARD)

def cmd_help(chat_id):
    if get_enabled(chat_id):
        send_msg(chat_id, USAGE, keyboard=SEARCH_KEYBOARD)
    else:
        send_msg(chat_id, USAGE, keyboard=START_KEYBOARD)

def cmd_setShop(chat_id, shop_name):
    shop_id = switch_shop_code(shop_name)
    if get_enabled(chat_id):
        set_shop(chat_id, shop_id)
        if shop_id == u'All':
            send_msg(chat_id, u'현재 검색 대상은 전체 매장입니다.', keyboard=SEARCH_KEYBOARD)
        else:
            send_msg(chat_id, u'현재 검색 대상은 ' + shop_name + u'입니다.', keyboard=SEARCH_KEYBOARD)
    else:
        send_msg(chat_id, u'먼저 봇을 활성화시켜주시기 바랍니다.', keyboard=START_KEYBOARD)

def cmd_getShop(chat_id):
    if get_enabled(chat_id):
        shop_name = switch_shop_name(get_shop(chat_id))
        send_msg(chat_id, u'현재 검색 대상은 ' + shop_name + u'입니다.', keyboard=SEARCH_KEYBOARD)
    else:
        send_msg(chat_id, u'먼저 봇을 활성화시켜주시기 바랍니다.', keyboard=START_KEYBOARD)

def cmd_broadcast(chat_id, text):
    send_msg(chat_id, u'Broadcast Messages.')
    broadcast(text)

def cmd_echo(chat_id, text, reply_to):
    send_msg(chat_id, text, reply_to=reply_to)

def cmd_search(chat_id, text, page):
    # send_msg(chat_id, u'검색 중입니다. 잠시만 기다려주세요')

    while True:
        reply = get_url(chat_id, text, page)
        temp = u'page: ' + unicode(page) + u', reply: ' + unicode(len(reply))
        print(temp)
        page = page - 1
        if len(reply) < 1000:
            break

    send_msg(chat_id, reply, keyboard=SEARCH_KEYBOARD)

def get_url(chat_id, title, page):
    url = ALADIN_URL
    url += 'SearchWord='
    url += title
    if (not (get_shop(chat_id) == u'All')):
        url += '&keytag='
        url += get_shop(chat_id)
    url += '&x=0&y=0'
    url += '&ViewRowCount='
    url += str(page)
    quote_url = urllib.quote(url.decode('utf-8').encode('cp949'), safe=':/?=&')
    send_msg(chat_id, quote_url)
    return make_connection(chat_id, quote_url, title)

def make_connection(chat_id, url, title):
    tried = 0
    connected = False
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    while not connected:
        try:
            res = browser.open(url)
            response = res.read()
            print(len(response))
            connected = True
            no_result = True
            soup = BeautifulSoup(response, 'html.parser')
            title = '*Search Result* - _' + title + '_\n' + url
            first_shop = True
            for x in soup.findAll(True, {'class': ['bo3', 'usedshop_off_text3']}):
                if (x.name == 'b'):
                    first_shop = True
                    no_result = False
                    title += '\n\n'
                    title = title + '*' + str(x.string) + '*'
                if (x.name == 'a'):
                    if (first_shop):
                        title += '\n - '
                        title += str(x.string)
                        first_shop = False
                    else:
                        title += ', '
                        title += str(x.string)
            if (no_result):
                title += '\n\n'
                title += '*검색 결과가 없습니다.*'
            return title
        except mechanize.HTTPError as e:
            send_msg(chat_id, e.reason.args, keyboard=SEARCH_KEYBOARD)
            tried += 1
            if tried > 4:
                exit()
            sleep(30)
        except mechanize.URLError as e:
            send_msg(chat_id, e.reason.args, keyboard=SEARCH_KEYBOARD)
            tried += 1
            if tried > 4:
                exit()
            sleep(30)
        except Exception as e:
            send_msg(chat_id, e.message, keyboard=SEARCH_KEYBOARD)

def switch_shop_code(shop_name):
    return {
        u'전체': u'All',
        u'강남점': u'A6',
        u'건대점': u'B5',
        u'광주점': u'A7',
        u'노원점': u'C0',
        u'대구동성로점': u'B0',
        u'대구상인점': u'D2',
        u'대전시청역점': u'C9',
        u'대전은행점': u'B4',
        u'대학로점': u'A8',
        u'부산경성대, 부경대역점': u'D7',
        u'부산서면점': u'D6',
        u'부산센텀점': u'D1',
        u'부천점': u'B1',
        u'북수원홈플러스점': u'D5',
        u'분당서현점': u'A5',
        u'분당야탑점': u'D4',
        u'산본점': u'B6',
        u'수원점': u'B9',
        u'수유점': u'D0',
        u'신림점': u'B3',
        u'신촌점': u'A4',
        u'연신내점': u'C6',
        u'울산점': u'A9',
        u'인천계산홈플러스점': u'D8',
        u'일산점': u'B7',
        u'잠실롯데타워점': u'C7',
        u'잠실신천점': u'C3',
        u'전주점': u'B2',
        u'종로점': u'A2',
        u'천안점': u'C5',
        u'청주점': u'C1',
        u'합정점': u'C8'
    }.get(shop_name, u'All')

def switch_shop_name(shop_id):
    return {
        u'All': u'전체',
        u'A6': u'강남점',
        u'B5': u'건대점',
        u'A7': u'광주점',
        u'C0': u'노원점',
        u'B0': u'대구동성로점',
        u'D2': u'대구상인점',
        u'C9': u'대전시청역점',
        u'B4': u'대전은행점',
        u'A8': u'대학로점',
        u'D7': u'부산경성대, 부경대역점',
        u'D6': u'부산서면점',
        u'D1': u'부산센텀점',
        u'B1': u'부천점',
        u'D5': u'북수원홈플러스점',
        u'A5': u'분당서현점',
        u'D4': u'분당야탑점',
        u'B6': u'산본점',
        u'B9': u'수원점',
        u'D0': u'수유점',
        u'B3': u'신림점',
        u'A4': u'신촌점',
        u'C6': u'연신내점',
        u'A9': u'울산점',
        u'D8': u'인천계산홈플러스점',
        u'B7': u'일산점',
        u'C7': u'잠실롯데타워점',
        u'C3': u'잠실신천점',
        u'B2': u'전주점',
        u'A2': u'종로점',
        u'C5': u'천안점',
        u'C1': u'청주점',
        u'C8': u'합정점'
    }.get(shop_id, u'전체')

# 10257
# no response
# keyword = "토플"
# cmd_search("test", keyword)

# 9226
# response ok
# keyword = "좌"
# cmd_search("test", keyword)

# 9602
# no response
# keyword = "너"
# cmd_search("test", keyword)

keyword = "토플"
page = 50
testurl = "http://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=UsedStore&SearchWord=%C5%E4%C7%C3&x=0&y=0&ViewRowCount=50"
cmd_search("test", keyword, page)

# http://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=UsedStore&SearchWord=%25C5%25E4%25C7%25C3&x=0&y=0&ViewRowCount=50
# http://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=UsedStore&SearchWord=%C5%E4%C7%C3&x=0&y=0&ViewRowCount=50
# http://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=UsedStore&SearchWord=%C5%E4%C7%C3&x=0&y=0&ViewRowCount=50