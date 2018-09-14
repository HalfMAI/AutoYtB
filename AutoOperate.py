from bilibiliProxy import BilibiliProxy
from subprocessOp import _forwardStream_sync
import utitls

def bilibiliStartLive(channelId, room_title, area_id=None):
    curSub = utitls.getSubInfoWithSubChannelId(channelId)
    curBiliAccCookie = curSub['bilibili_cookiesStr']

    tmp_area_id = area_id
    if tmp_area_id == None:
        tmp_area_id = curSub['bilibili_areaid']

    b = BilibiliProxy(curBiliAccCookie)
    t_room_id = b.getLiveRoomId()
    b.stopLive(t_room_id)   #stop first maybe useful?

    b.updateRoomTitle(t_room_id, room_title)
    rtmp_link = b.startLive(t_room_id, tmp_area_id)
    return b, rtmp_link


def Async_forwardToBilibili(channelId, link, room_title='Testing Title', area_id=None):
    utitls.runFuncAsyncProcess(_forwardToBilibili_Sync, (link, room_title, area_id))
def _forwardToBilibili_Sync(channelId, link, room_title, area_id=None):
    b, t_room_id, rtmp_link = bilibiliStartLive(room_title, area_id)
    _forwardStream_sync(link, rtmp_link)
    b.stopLive(t_room_id)
