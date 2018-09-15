import requests
from utitls import configJson, myLogger
import traceback

def subscribe(callbackURL, channel_id):
    _requsetBase(callbackURL, channel_id, 'subscribe')

def unsubscribe(callbackURL, channel_id):
    _requsetBase(callbackURL, channel_id, 'unsubscribe')

def _requsetBase(callbackURL, channel_id, mode):
    response = _basePost(
                'https://pubsubhubbub.appspot.com/subscribe',
                {
                    'hub.callback': callbackURL,
                    'hub.topic': 'https://www.youtube.com/xml/feeds/videos.xml?channel_id=' + channel_id,
                    'hub.verify': 'sync',
                    'hub.mode': mode,
                    'hub.verify_token': '',
                    'hub.secret': configJson().get('subSecert', ''),
                    'hub.lease_seconds': ''
                }
            )
    return _baseRequestProcess(response)


def getYoutubeVideoInfo(youtubeURL):
    response = _baseGet('https://www.youtube.com/oembed?url=%s&format=json' % youtubeURL)
    resJson = _baseRequestProcess(response)
    title = resJson.get("title")
    thumbnail_url = resJson.get('thumbnail_url')
    return title, thumbnail_url


def isTwitcastingLiving(id):
    res = _baseGet('http://api.twitcasting.tv/api/livestatus?user=' + id)
    if res == None:
        return False
    if '"islive":true' in res.text:
        return True
    return False

def _baseGet(self, url):
    try:
        myLogger("GET URL:%s--" % url)
        response = requests.get(url, timeout=30)
    except Exception as e:
        myLogger(str(e))
        myLogger(traceback.format_exc())
        return None
    return _baseRequestProcess(response)


def _basePost(url, data):
    try:
        myLogger("POST URL:%s--" % url)
        myLogger("DATA    :%s--" % data)
        response = requests.post(url, data=data, timeout=30)
    except Exception as e:
        myLogger(str(e))
        myLogger(traceback.format_exc())
        return None
    return _baseRequestProcess(response)

def _baseRequestProcess(response):
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
