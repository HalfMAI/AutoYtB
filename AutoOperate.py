import utitls
import time
import traceback
import os
import signal

from login import login
from bilibiliProxy import BilibiliProxy
from subprocessOp import _forwardStream_sync, resolveStreamToM3u8, async_forwardStream
import questInfo
from myRequests import subscribe, getUpcomingLiveVideos, getYoutubeLiveStreamInfo
import scheduler

def getBilibiliProxy(subObj):
    curSub = subObj
    curBiliAccCookie = curSub.get('bilibili_cookiesStr', "")
    b = BilibiliProxy(curBiliAccCookie)
    if b.getAccInfo() == None:
        #relogin
        if curSub['login_type'] == 'account':
            tmp_username, tmp_password = curSub.get('username'), curSub.get('password')
            if tmp_username and tmp_password:
                curSub['bilibili_cookiesStr'] = login(tmp_username, tmp_password)
                utitls.setSubInfoWithKey('username', tmp_username, curSub)
                time.sleep(1)
                return getBilibiliProxy(subObj)                         #retry the StartLive. TODO Maybe limit the retry time?
    else:
        return b

def bilibiliStartLive(subscribe_obj, room_title, area_id=None):
    curSub = subscribe_obj

    tmp_area_id = area_id
    if tmp_area_id == None:
        tmp_area_id = curSub.get('bilibili_areaid', '33')

    b = getBilibiliProxy(curSub)

    t_room_id = b.getLiveRoomId()
    t_cur_blive_url = 'https://live.bilibili.com/' + t_room_id
    curSub['cur_blive_url'] = t_cur_blive_url
    # b.stopLive(t_room_id)   #Just don't care the Live status, JUST STARTLIVE
    t_b_title = curSub.get('change_b_title')
    if t_b_title:
        b.updateRoomTitle(t_room_id, t_b_title)
    rtmp_link = b.startLive(t_room_id, tmp_area_id)

    if curSub.get('auto_send_dynamic') and rtmp_link and questInfo._getObjWithRTMPLink(rtmp_link) is None:
        if curSub.get('dynamic_template'):
            b.send_dynamic((curSub['dynamic_template']).replace('${roomUrl}', t_cur_blive_url))
        else:
            b.send_dynamic('转播开始了哦~')
    return b, t_room_id, rtmp_link

__g_try_bili_quest_list = []
def Async_forwardToBilibili(subscribe_obj, input_link, room_title='Testing Title', area_id=None, isSubscribeQuest=True):
    utitls.runFuncAsyncThread(_forwardToBilibili_Sync, (subscribe_obj, input_link, room_title, area_id, isSubscribeQuest))
def _forwardToBilibili_Sync(subscribe_obj, input_link, room_title, area_id=None, isSubscribeQuest=True):
    global __g_try_bili_quest_list
    utitls.myLogger('CURRENT Async_forwardToBilibili:\n{}'.format(__g_try_bili_quest_list))

    input_quest = "{}_{}".format(subscribe_obj.get('mark', ""), input_link)
    if input_quest in __g_try_bili_quest_list:
        utitls.myLogger('current input quest is already RUNNING:\n{}'.format(input_quest))
        return

    __g_try_bili_quest_list.append(input_quest)
    utitls.myLogger('APPEND QUEST Async_forwardToBilibili:\n{}'.format(input_quest))
    resolveURLOK = False

    if isSubscribeQuest:
        tmp_retryTime = 60 * 10      #retry 10 hours, Some youtuber will startLive before few hours
    else:
        tmp_retryTime = 3           # if not subscribe quest, just try 3 minutes
    while tmp_retryTime > 0:
        if 'youtube.com/' in input_link or 'youtu.be/' in input_link:
            tmp_is_log = (tmp_retryTime % 60 == 0)  # log every 60 minus
            m3u8Link, title, err, errcode = resolveStreamToM3u8(input_link, tmp_is_log)
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
        elif utitls.checkIsSupportForwardLink(input_link):
            resolveURLOK = True
            break
        else:
            if isSubscribeQuest:
                utitls.myLogger('_forwardToBilibili_Sync LOG: Unsupport ForwardLink:' + input_link)
                __g_try_bili_quest_list.remove(input_quest)
                return
            else:
                resolveURLOK = True     # if it's not subscribeQuest, just start living
                break

    if resolveURLOK:
        tmp_acc_mark = subscribe_obj.get('mark', None)
        if tmp_acc_mark:
            quest = questInfo._getObjWithAccMark(tmp_acc_mark)
            if quest == None:
                b, t_room_id, rtmp_link = bilibiliStartLive(subscribe_obj, room_title, area_id)
                # force stream
                _forwardStream_sync(input_link, rtmp_link, isSubscribeQuest, subscribe_obj)
            else:
                utitls.myLogger("THIS ACC IS CURRENTLY STREAMING :{}, SKIP THE QUEST".format(tmp_acc_mark))

    if input_quest in __g_try_bili_quest_list:
        utitls.myLogger('REMOVE QUEST Async_forwardToBilibili:\n{}'.format(input_quest))
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
            tmp_subscribeId_list = item.get('youtubeChannelId', "").split(',')
            for tmp_subscribeId in tmp_subscribeId_list:
                if tmp_subscribeId != "":
                    tmp_callback_url = 'http://{}:{}/subscribe'.format(ip, port)
                    subscribe(tmp_callback_url, tmp_subscribeId)
        time.sleep(3600 * 24 * 4)   #update the subscribe every 4 Days

def clearOldQuests():
    questInfo.initQuestList()

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

def perparingAllComingVideos():
    utitls.runFuncAsyncThread(perparingAllComingVideos_sync, ())
def perparingAllComingVideos_sync():
    time.sleep(2)   #wait the server start preparing
    subscribeList = utitls.configJson().get('subscribeList', [])
    for subObj in subscribeList:
        tmp_subscribeId_list = subObj.get('youtubeChannelId', "").split(',')
        for tmp_subscribeId in tmp_subscribeId_list:
            if tmp_subscribeId != "":
                videoIds = getUpcomingLiveVideos(tmp_subscribeId)
                for vid in videoIds:
                    item = getYoutubeLiveStreamInfo(vid)
                    if item:
                        liveStreamingDetailsDict = item.get('liveStreamingDetails', None)
                        if liveStreamingDetailsDict:
                            tmp_is_live = liveStreamingDetailsDict.get('concurrentViewers', None)
                            tmp_actual_start_time = liveStreamingDetailsDict.get('actualStartTime', None)
                            tmp_scheduled_start_time = liveStreamingDetailsDict.get('scheduledStartTime', None)
                            tmp_is_end = liveStreamingDetailsDict.get('actualEndTime', None)

                            if tmp_scheduled_start_time and tmp_is_end == None and tmp_is_live == None and tmp_actual_start_time == None:
                                tmp_acc_mark = subObj.get('mark', "")
                                tmp_area_id = subObj.get('area_id', '33')
                                job_id = 'Acc:{},VideoID:{}'.format(tmp_acc_mark, vid)

                                snippet = item.get('snippet', {})
                                tmp_title = snippet.get('title', "")
                                tmp_live_link = 'https://www.youtube.com/watch?v={}'.format(vid)
                                scheduler.add_date_job(tmp_scheduled_start_time, job_id, Async_forwardToBilibili,
                                    (subObj, tmp_live_link, tmp_title, tmp_area_id)
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
