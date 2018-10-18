import hashlib
import hmac
import re
import struct
import time
import uuid

from base64 import urlsafe_b64encode
from binascii import unhexlify

from Crypto.Cipher import AES

import requests
# from requests import Response
# from requests.adapters import BaseAdapter


UA_CHROME = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36")


class AbemaTVLicenseAdapter():
    '''
    Handling abematv-license:// protocol to get real video key_data.
    '''

    STRTABLE = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    HKEY = b"3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E"

    _MEDIATOKEN_API = "https://api.abema.io/v1/media/token"

    _LICENSE_API = "https://license.abema.io/abematv-hls"

    # _MEDIATOKEN_SCHEMA = validate.Schema({u"token": validate.text})
    #
    # _LICENSE_SCHEMA = validate.Schema({u"k": validate.text,
    #                                    u"cid": validate.text})

    def __init__(self, session):
        self._session = session
        self.ticketDict = {}

    def init_user(self, deviceid, usertoken):
        self.deviceid = deviceid
        self.usertoken = usertoken

    def _get_videokey_from_ticket(self, ticket):
        ticket = ticket.decode('utf-8') if isinstance(ticket, (bytes, bytearray)) else ticket
        params = {
            "osName": "android",
            "osVersion": "6.0.1",
            "osLang": "ja_JP",
            "osTimezone": "Asia/Tokyo",
            "appId": "tv.abema",
            "appVersion": "3.27.1"
        }
        auth_header = {"Authorization": "Bearer " + self.usertoken}
        res = self._session.get(self._MEDIATOKEN_API, params=params,
                                     headers=auth_header)
        jsonres = res.json()
        mediatoken = jsonres['token']

        res = self._session.post(self._LICENSE_API,
                                      params={"t": mediatoken},
                                      json={"kv": "a", "lt": ticket})
        jsonres = res.json()
        cid = jsonres['cid']
        k = jsonres['k']


        res = sum([self.STRTABLE.find(k[i]) * (58 ** (len(k) - 1 - i))
                  for i in range(len(k))])
        encvideokey = struct.pack('>QQ', res >> 64, res & 0xffffffffffffffff)

        # HKEY:
        # RC4KEY = unhexlify('DB98A8E7CECA3424D975280F90BD03EE')
        # RC4DATA = unhexlify(b'D4B718BBBA9CFB7D0192A58F9E2D146A'
        #                     b'FC5DB29E4352DE05FC4CF2C1005804BB')
        # rc4 = ARC4.new(RC4KEY)
        # HKEY = rc4.decrypt(RC4DATA)
        h = hmac.new(unhexlify(self.HKEY),
                     (cid + self.deviceid).encode("utf-8"),
                     digestmod=hashlib.sha256)
        enckey = h.digest()

        aes = AES.new(enckey, AES.MODE_ECB)
        rawvideokey = aes.decrypt(encvideokey)

        return rawvideokey

    def get_videokey_from_ticket(self, ticket):
        ret_videokey = self.ticketDict.get(ticket, None)
        if ret_videokey:
            return ret_videokey
        else:
            # cache the key
            ret_videokey = self._get_videokey_from_ticket(ticket)
            self.ticketDict[ticket] = ret_videokey
            return ret_videokey


class AbemaTV():
    '''
    Abema.tv https://abema.tv/
    Note: Streams are geo-restricted to Japan

    '''
    _url_re = re.compile(r"""https://abema\.tv/(
        now-on-air/(?P<onair>[^\?]+)
        |
        video/episode/(?P<episode>[^\?]+)
        |
        channels/.+?/slots/(?P<slots>[^\?]+)
        )""", re.VERBOSE)

    _CHANNEL = "https://api.abema.io/v1/channels"

    _USER_API = "https://api.abema.io/v1/users"

    _PRGM_API = "https://api.abema.io/v1/video/programs/{0}"

    _SLOTS_API = "https://api.abema.io/v1/media/slots/{0}"

    _PRGM3U8 = "https://vod-abematv.akamaized.net/program/{0}/playlist.m3u8"

    _SLOTM3U8 = "https://vod-abematv.akamaized.net/slot/{0}/playlist.m3u8"

    SECRETKEY = (b"v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9B"
                 b"Rbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$"
                 b"k9cD=3TxwWe86!x#Zyhe")

    # _USER_SCHEMA = validate.Schema({u"profile": {u"userId": validate.text},
    #                                 u"token": validate.text})
    #
    # _CHANNEL_SCHEMA = validate.Schema({u"channels": [{u"id": validate.text,
    #                                   "name": validate.text,
    #                                    "playback": {validate.optional(u"dash"):
    #                                                 validate.text,
    #                                                 u"hls": validate.text}}]})
    #
    # _PRGM_SCHEMA = validate.Schema({u"label": {validate.optional(u"free"): bool
    #                                            }})
    #
    # _SLOT_SCHEMA = validate.Schema({u"slot": {u"flags": {
    #                                 validate.optional("timeshiftFree"): bool}}}
    #                                )

    @classmethod
    def can_handle_url(cls, url):
        return cls._url_re.match(url) is not None

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': UA_CHROME})
        self.aba = AbemaTVLicenseAdapter(self.session)

    def _generate_applicationkeysecret(self, deviceid):
        deviceid = deviceid.encode("utf-8")  # for python3
        # plus 1 hour and drop minute and secs
        # for python3 : floor division
        ts_1hour = (int(time.time()) + 60 * 60) // 3600 * 3600
        time_struct = time.gmtime(ts_1hour)
        ts_1hour_str = str(ts_1hour).encode("utf-8")

        h = hmac.new(self.SECRETKEY, digestmod=hashlib.sha256)
        h.update(self.SECRETKEY)
        tmp = h.digest()
        for i in range(time_struct.tm_mon):
            h = hmac.new(self.SECRETKEY, digestmod=hashlib.sha256)
            h.update(tmp)
            tmp = h.digest()
        h = hmac.new(self.SECRETKEY, digestmod=hashlib.sha256)
        h.update(urlsafe_b64encode(tmp).rstrip(b"=") + deviceid)
        tmp = h.digest()
        for i in range(time_struct.tm_mday % 5):
            h = hmac.new(self.SECRETKEY, digestmod=hashlib.sha256)
            h.update(tmp)
            tmp = h.digest()

        h = hmac.new(self.SECRETKEY, digestmod=hashlib.sha256)
        h.update(urlsafe_b64encode(tmp).rstrip(b"=") + ts_1hour_str)
        tmp = h.digest()

        for i in range(time_struct.tm_hour % 5):  # utc hour
            h = hmac.new(self.SECRETKEY, digestmod=hashlib.sha256)
            h.update(tmp)
            tmp = h.digest()

        return urlsafe_b64encode(tmp).rstrip(b"=").decode("utf-8")


    def init_usertoken(self):
        deviceid = str(uuid.uuid4())
        appkeysecret = self._generate_applicationkeysecret(deviceid)
        json_data = {"deviceId": deviceid,
                     "applicationKeySecret": appkeysecret}
        res = self.session.post(self._USER_API, json=json_data)
        jsonres = res.json()
        self.usertoken = jsonres['token']  # for authorzation
        self.aba.init_user(deviceid, self.usertoken)

    def get_videokey_from_ticket(self, ticket):
        return self.aba.get_videokey_from_ticket(ticket)
