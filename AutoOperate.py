import utitls
import time
import traceback
import os
import signal

from login import login
from bilibiliProxy import BilibiliProxy
from subprocessOp import _forwardStream_sync, _getYoutube_m3u8_sync, async_forwardStream
import questInfo
from myRequests import subscribe

def bilibiliStartLive(subscribe_obj, room_title, area_id=None):
    curSub = subscribe_obj
    curBiliAccCookie = curSub.get('bilibili_cookiesStr', "")

    tmp_area_id = area_id
    if tmp_area_id == None:
        tmp_area_id = curSub.get('bilibili_areaid', '33')

    b = BilibiliProxy(curBiliAccCookie)
    if b.getAccInfo() == None:
        #relogin
        if curSub['login_type'] == 'account':
            tmp_username, tmp_password = curSub.get('username'), curSub.get('password')
            if tmp_username and tmp_password:
                curSub['bilibili_cookiesStr'] = login(tmp_username, tmp_password)
                utitls.setSubInfoWithKey('username', tmp_username, curSub)
                bilibiliStartLive(curSub, room_title, area_id)
                return #retry the StartLive. TODO Maybe limit the retry time?

    t_room_id = b.getLiveRoomId()
    # b.stopLive(t_room_id)   #Just don't care the Live status, JUST STARTLIVE
    # b.updateRoomTitle(t_room_id, room_title) #Maybe just ignore changing the title
    rtmp_link = b.startLive(t_room_id, tmp_area_id)

    if curSub.get('auto_send_dynamic') and rtmp_link and questInfo._getObjWithRTMPLink(rtmp_link) is None:
        if curSub.get('dynamic_template'):
            b.send_dynamic((curSub['dynamic_template']).replace('${roomUrl}', 'https://live.bilibili.com/' + t_room_id))
        else:
            b.send_dynamic('转播开始了哦~')
    return b, t_room_id, rtmp_link

__g_try_bili_quest_list = []
def Async_forwardToBilibili(subscribe_obj, input_link, room_title='Testing Title', area_id=None, isSubscribeQuest=True):
    utitls.runFuncAsyncThread(_forwardToBilibili_Sync, (subscribe_obj, input_link, room_title, area_id, isSubscribeQuest))
def _forwardToBilibili_Sync(subscribe_obj, input_link, room_title, area_id=None, isSubscribeQuest=True):
    global __g_try_bili_quest_list
    utitls.myLogger('CURRENT Async_forwardToBilibili:\n{}'.format(__g_try_bili_quest_list))

    input_quest = input_link + subscribe_obj.get('mark', "")
    if input_quest in __g_try_bili_quest_list:
        utitls.myLogger('current input quest is already RUNNING:\n{}'.format(input_quest))
        return

    __g_try_bili_quest_list.append(input_quest)
    resolveURLOK = False

    if isSubscribeQuest:
        tmp_retryTime = 60 * 10      #retry 10 hours, Some youtuber will startLive before few hours
    else:
        tmp_retryTime = 3           # if not subscribe quest, just try 3 times
    while tmp_retryTime > 0:
        if 'youtube.com/' in input_link or 'youtu.be/' in input_link:
            m3u8Link, title, err, errcode = _getYoutube_m3u8_sync(input_link, False)
            if errcode == 999:
                # this is just a video upload, so just finish it
                __g_try_bili_quest_list.remove(input_quest)
                utitls.myLogger('_forwardToBilibili_Sync LOG: This is not a Live Videos:' + input_link)
                return
            elif errcode == 0:
                # input_link = m3u8Link   #just to check is can use, _forwardStream_sync will access the title and questInfo
                resolveURLOK = True
                break
            else:
                tmp_retryTime -= 1
        else:
            if isSubscribeQuest:
                utitls.myLogger('_forwardToBilibili_Sync LOG: Unsupport ForwardLink:' + input_link)
                __g_try_bili_quest_list.remove(input_quest)
                return
            else:
                resolveURLOK = True     # if it's not subscribeQuest, just start living
                break

    if resolveURLOK:
        b, t_room_id, rtmp_link = bilibiliStartLive(subscribe_obj, room_title, area_id)
        if rtmp_link:   #kill the old proccess
            tmp_quest = questInfo._getObjWithRTMPLink(rtmp_link)
            if tmp_quest != None:
                try:
                    os.kill(tmp_quest.get('pid', None), signal.SIGKILL)
                except Exception:
                    utitls.myLogger(traceback.format_exc())
                time.sleep(5)
            # force stream
            _forwardStream_sync(input_link, rtmp_link, isSubscribeQuest)

    if input_quest in __g_try_bili_quest_list:
        __g_try_bili_quest_list.remove(input_quest)



def Async_subscribeTheList():
    utitls.runFuncAsyncThread(subscribeTheList_sync, ())
def subscribeTheList_sync():
    time.sleep(10)   #wait the server start preparing
    while True:
        subscribeList = utitls.configJson().get('subscribeList', [])
        ip = utitls.configJson().get('serverIP')
        port = utitls.configJson().get('serverPort')
        for item in subscribeList:
            tmp_subscribeId = item.get('youtubeChannelId', "")
            if tmp_subscribeId != "":
                tmp_callback_url = 'http://{}:{}/subscribe'.format(ip, port)
                subscribe(tmp_callback_url, tmp_subscribeId)
        time.sleep(3600 * 24 * 4)   #update the subscribe every 4 Days


def restartOldQuests():
    time.sleep(3)   #wait the server start preparing
    for quest in questInfo._getQuestList():
        tmp_pid = quest.get('pid')
        if tmp_pid:
            try:
                os.kill(tmp_pid, 0)     #just check is the pid Running
            except OSError:
                # if the pid was killed
                rtmp_link = quest.get('rtmpLink')
                questInfo.updateQuestInfo('isRestart', True, rtmp_link)
                async_forwardStream(
                    quest.get('forwardLinkOrign'),
                    rtmp_link,
                    quest.get('isSubscribeQuest')
                )


def preparingAllAccountsCookies():
    utitls.runFuncAsyncThread(preparingAllAccountsCookies_sync, ())
def preparingAllAccountsCookies_sync():
    time.sleep(2)   #wait the server start preparing
    sub_list = utitls.configJson().get('subscribeList', [])
    for curSub in sub_list:
        if curSub.get('login_type', "") == 'account' and curSub.get('bilibili_cookiesStr', "") == "":
            tmp_username, tmp_password = curSub.get('username'), curSub.get('password')
            if tmp_username and tmp_password:
                curSub['bilibili_cookiesStr'] = login(tmp_username, tmp_password)
                utitls.setSubInfoWithKey('username', tmp_username, curSub)
                time.sleep(5)   # wait for the last browser memory release
