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


g_key = 'AIzaSyBQQK9THRp1OzsGtbcIdgmmAn3MCP77G10'     #youtube API key, it can call 1000k/3 times, it can be public. 1 call cost 3.
def getYoutubeLiveStreamInfo(vidoeID):
    global g_key
    resJson = _baseGet('https://www.googleapis.com/youtube/v3/videos?id={}&part=liveStreamingDetails,snippet&key={}'.format(vidoeID, g_key))
    if resJson:
        items = resJson.get('items')
        if len(items) > 1:
            return items[0].get('id')
        else:
            return None
    else:
        return None

def getYoutubeLiveVideoInfoFromChannelID(channelID):
    global g_key
    resJson = _baseGet('https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={}&eventType=live&type=video&key={}'.format(channelID, g_key))
    if resJson:
        items = resJson.get('items')
        if len(items) > 1:
            item = items[0]
            videoId = item.get('id', {}).get('videoId')
            if videoId:
                item = getYoutubeLiveStreamInfo(videoId)
                return item
        else:
            return None
    else:
        return None



def isTwitcastingLiving(id):
    res = _baseGet('http://api.twitcasting.tv/api/livestatus?user=' + id)
    if res == None:
        return False
    if '"islive":true' in res.text:
        return True
    return False

def _baseGet(url):
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
