from bilibiliProxy import BilibiliProxy
from subprocessOp import _forwardStream_sync, _getYotube_m3u8_sync
import utitls
import time
import traceback
import os
import signal

import questInfo

def bilibiliStartLive(channelId, room_title, area_id=None):
    curSub = utitls.getSubInfoWithSubChannelId(channelId)
    curBiliAccCookie = curSub['bilibili_cookiesStr']

    tmp_area_id = area_id
    if tmp_area_id == None:
        tmp_area_id = curSub['bilibili_areaid']

    b = BilibiliProxy(curBiliAccCookie)
    t_room_id = b.getLiveRoomId()
    # b.stopLive(t_room_id)   #Just don't care the Live status, JUST STARTLIVE

    b.updateRoomTitle(t_room_id, room_title)
    rtmp_link = b.startLive(t_room_id, tmp_area_id)
    if curSub['auto_send_dynamic'] and rtmp_link and questInfo._getObjWithRTMPLink(rtmp_link) is None:
        if curSub['dynamic_template']:
            b.send_dynamic(curSub['dynamic_template'])
        else:
            b.send_dynamic('转播开始了哦~')
    return b, t_room_id, rtmp_link


def Async_forwardToBilibili(channelId, link, room_title='Testing Title', area_id=None, isSubscribeQuest=True):
    utitls.runFuncAsyncThread(_forwardToBilibili_Sync, (channelId, link, room_title, area_id, isSubscribeQuest))
def _forwardToBilibili_Sync(channelId, link, room_title, area_id=None, isSubscribeQuest=True):
    resloveURLOK = False
    tmp_retryTime = 10
    while tmp_retryTime > 0:
        if 'youtube.com/' in link or 'youtu.be/' in link:
            m3u8Link, err, errcode = _getYotube_m3u8_sync(link)
            if errcode == 0:
                link = m3u8Link
                resloveURLOK = True
                break
            else:
                tmp_retryTime -= 1
                time.sleep(60)
        else:
            utitls.myLogger('_forwardToBilibili_Sync LOG: Unsupport ForwardLink:' + link)
            return

    if resloveURLOK:
        b, t_room_id, rtmp_link = bilibiliStartLive(channelId, room_title, area_id)
        if rtmp_link:
            tmp_quest = questInfo._getObjWithRTMPLink(rtmp_link)
            if tmp_quest != None:
                try:
                    os.kill(tmp_quest.get('pid', None), signal.SIGKILL)
                except Exception:
                    utitls.myLogger(traceback.format_exc())
                questInfo.removeQuest(rtmp_link)
            # force stream
            _forwardStream_sync(link, rtmp_link, isSubscribeQuest)
