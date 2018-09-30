import traceback

import requests
from http.cookies import SimpleCookie
from utitls import myLogger

class BilibiliProxy:

    def __init__(self, cookies_str):
        self.session = requests.session()
        self.csrf_token = None
        self._initWithCookies(cookies_str)
        if self.getAccInfo() == None:
            myLogger('ERROR: Cookie login failed!!!!!')
            #TODO maybe relogin?

            
    def _initWithCookies(self, cookies_str):
        cookie = SimpleCookie()
        cookie.load(cookies_str)
        cookies_dict = {}
        for key, morsel in cookie.items():
            cookies_dict[key] = morsel.value

        cookiejar = requests.utils.cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
        self.csrf_token = cookies_dict.get('bili_jct')

        self.session.cookies = cookiejar



    def _baseRequestProcess(self, response):
        if response == None:
            return None
        try:
            myLogger("Request URL:%s-----------------" % response.request.url)
            myLogger("Method:%s, Code:%s,\n text:%s" % (response.request.method, str(response.status_code), response.text))
            if response.status_code == 200:
                try:
                    return response.json()
                except Exception:
                    return None
            else:
                return None
        except Exception as e:
            myLogger("request Exception:%s" % str(e))
            myLogger(traceback.format_exc())
            return None


    def _baseGet(self, url):
        try:
            myLogger("GET URL:%s--" % url)
            response = self.session.get(url, timeout=30)
        except Exception as e:
            myLogger(str(e))
            myLogger(traceback.format_exc())
            return None

        return self._baseRequestProcess(response)


    def _basePost(self, url, data):
        try:
            myLogger("POST URL:%s--" % url)
            myLogger("DATA    :%s--" % data)
            response = self.session.post(url, data=data, timeout=30)
        except Exception as e:
            myLogger(str(e))
            myLogger(traceback.format_exc())
            return None
        return self._baseRequestProcess(response)


    def startLive(self, room_id, area_id):
        resDict = self._basePost(
            'https://api.live.bilibili.com/room/v1/Room/startLive',
            {
                'room_id': room_id,
                'platform': 'pc',
                'area_v2': area_id,
                'csrf_token': self.csrf_token
            }
        )
        if resDict:
            if resDict['code'] == 0:
                rtmp_link = resDict['data']['rtmp']['addr'] + resDict['data']['rtmp']['code']
                myLogger("Current RTMP_LINK:%s" % rtmp_link)
                return rtmp_link
        else:
            return None


    def stopLive(self, room_id):
        resDict = self._basePost(
            'https://api.live.bilibili.com/room/v1/Room/stopLive',
            {
                'room_id': room_id,
                'platform': 'pc',
                'csrf_token': self.csrf_token
            }
        )
        if resDict:
            if resDict['code'] != 0:
                myLogger('ERROR: StopLive Failed')


    def getLiveRoomId(self):
        resDict = self._baseGet('https://api.live.bilibili.com/i/api/liveinfo')
        if resDict:
            if resDict['code'] == 0:
                return resDict['data']['roomid']
            else:
                return None


    def updateRoomTitle(self, room_id, title):
        resDict = self._basePost(
            'https://api.live.bilibili.com/room/v1/Room/update',
            {
                'room_id': room_id,
                'title': title,
                'csrf_token': self.csrf_token
            }
        )
        if resDict:
            if resDict['code'] != 0:
                myLogger('ERROR: update room title Failed')


    def getAccInfo(self):
        resDict = self._baseGet('https://api.bilibili.com/x/member/web/account')
        if resDict:
            if resDict['code'] == 0:
                return resDict['data']
            else:
                myLogger('ERROR: Account no login')
                return None

    def send_dynamic(self, content):
        self._basePost(
            'http://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/repost',
            {
                'dynamic_id': '0',
                'type': '4',
                'rid': '0',
                'content': content,
                'at_uids': '',
                'ctrl': '[]',
                'csrf_token': self.csrf_token
            }
        )
