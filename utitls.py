import hmac
import hashlib
import secrets
import json
import datetime
from multiprocessing import Process

K_CONFIG_JSON_PATH = 'config.json'
k_LOG_PATH = 'mainLog.log'

def myLogger(logStr):
    resStr = str(datetime.datetime.now()) + "   " + str(logStr)
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

def configJson():
    with open(K_CONFIG_JSON_PATH, 'r', encoding='utf-8') as f:
        configDict = json.loads(f.read())

        # greate the secerts key
        if configDict.get('subSecert') == "":
            configDict['subSecert'] = secrets.token_hex(16)
            saveConfigJson(configDict)
        return configDict


def getSubInfoWithSubChannelId(channelId):
    ret = None
    for subscribe in configJson().get('subscribeList', []):
        if subscribe.get('youtubeChannelId') == channelId:
            ret = subscribe.get('bilibili_cookiesStr')
            break
    return ret


def saveConfigJson(config_dict):
    with open(K_CONFIG_JSON_PATH, 'w', encoding='utf-8') as wf:
        json.dump(config_dict, wf, indent=4, sort_keys=True)


def runFuncAsyncProcess(target_func, args):
    t = Process(target=target_func, args=args)
    t.start()
