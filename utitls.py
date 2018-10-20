import hmac
import hashlib
import secrets
import json
import datetime
import traceback
import re
import signal, psutil
import threading

K_MANUAL_JSON_PATH = 'manualRestream.json'
K_CONFIG_JSON_PATH = 'config.json'
k_LOG_PATH = 'mainLog.log'


def myLogger(logStr):
    resStr = str(datetime.datetime.now()) + " [MyLOGGER]  " + str(logStr)
    try:
        print(resStr)
    except Exception as e:
        print(e)
    with open(k_LOG_PATH, 'a+', encoding='utf-8') as tmpFile:
        tmpFile.write(resStr + '\n')

def verifySecert(verifyMsg, i_msg):
    i_msg = str.encode(i_msg) if isinstance(i_msg, str) else i_msg
    key = configJson().get('subSecert', '')
    key = str.encode(key)
    hexdig = hmac.new(key, msg=i_msg, digestmod=hashlib.sha1).hexdigest()

    print(verifyMsg, hexdig)
    return verifyMsg == hexdig

def remove_emoji(text):
    emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002700-\U000027BF"  # Dingbats
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
      parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
      return
    children = parent.children(recursive=True)
    for process in children:
      process.send_signal(sig)

def checkIsSupportForwardLink(forwardLink):
    check_list = [
        '.m3u8',
        'twitcasting.tv/',
        'youtube.com/', 'youtu.be/',
        'twitch.tv/',
        'showroom-live.com/'
    ]
    for word in check_list:
        if word in forwardLink:
            return True
    return False

def configJson():
    with open(K_CONFIG_JSON_PATH, 'r', encoding='utf-8') as f:
        configDict = json.loads(f.read())

        # greate the secerts key
        if configDict.get('subSecert') == "":
            configDict['subSecert'] = secrets.token_hex(16)
            saveConfigJson(configDict)
        return configDict


def getSubInfoWithSubChannelId(channelId):
    return getSubWithKey('youtubeChannelId', channelId)

def getSubWithKey(key, val):
    ret = None
    for subscribe in configJson().get('subscribeList', []):
        if subscribe.get(key) == val:
            ret = subscribe
            break
    return ret


def setSubInfoWithSubChannelId(channelId, subDict):
    setSubInfoWithKey('youtubeChannelId', channelId, subDict)

def setSubInfoWithKey(key, val, subDict):
    confDict = configJson()
    for subscribe in confDict.get('subscribeList', []):
        if subscribe.get(key) == val:
            subscribe.update(subDict)
            saveConfigJson(confDict)
            return


def saveConfigJson(config_dict):
    with open(K_CONFIG_JSON_PATH, 'w', encoding='utf-8') as wf:
        json.dump(config_dict, wf, indent=4, sort_keys=True)


def addManualSrc(srcNote, srcLink):
    tmp_dict = manualJson()
    src_dict = tmp_dict.get('src_dict', {})
    src_dict[srcNote] = srcLink
    tmp_dict['src_dict'] = src_dict
    saveManualJson(tmp_dict)

def addManualDes(desNote, desLink):
    tmp_dict = manualJson()
    des_dict = tmp_dict.get('des_dict', {})
    des_dict[desNote] = desLink
    tmp_dict['des_dict'] = des_dict
    saveManualJson(tmp_dict)


def manualJson():
    manualDict = {"src_dict":{}, "des_dict":{}}
    try:
        with open(K_MANUAL_JSON_PATH, 'r', encoding='utf-8') as f:
            manualDict = json.loads(f.read())
    except FileNotFoundError:
        saveManualJson(manualDict)
    return manualDict

def saveManualJson(manualDict):
    with open(K_MANUAL_JSON_PATH, 'w', encoding='utf-8') as wf:
        json.dump(manualDict, wf, indent=4, sort_keys=True)


def runFuncAsyncThread(target_func, args):
    try:
        t = threading.Thread(target=target_func, args=args)
        t.start()
    except Exception as e:
        myLogger(traceback.format_exc())
        myLogger(str(e))
