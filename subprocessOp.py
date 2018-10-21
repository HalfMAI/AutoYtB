import os
import subprocess
import time, datetime
import json
import traceback
import re

import utitls
import questInfo
import myRequests

def __runCMDSync(cmd, isLog=True):
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pid = p.pid
        if isLog:
            utitls.myLogger("CMD RUN START with PID:{}\nCMD: {}".format(pid, cmd))
        try:
            rtmpLink = cmd.partition('-f flv "')[2].partition('"')[0]   #get the first -f link
            if rtmpLink.startswith('rtmp://'):
                questInfo.updateQuestInfo('pid', pid, rtmpLink)
        except Exception: pass
        out, err = p.communicate()
        errcode = p.returncode
        if isLog:
            utitls.myLogger("CMD RUN END with PID:{}\nCMD: {}\nOUT: {}\nERR: {}\nERRCODE: {}".format(pid, cmd, out, err, errcode))
    except Exception as e:
        out, err, errcode = None, e, -1
        utitls.myLogger(traceback.format_exc())
    return out, err, errcode


def _getYoutube_m3u8_sync(youtubeLink, isLog=True):
    out, err, errcode = None, None, -1

    tmp_retryTime = 0
    while tmp_retryTime < 2:
        out, err, errcode = __runCMDSync('youtube-dl --no-check-certificate -j {}'.format(youtubeLink), isLog)
        out = out.decode('utf-8') if isinstance(out, (bytes, bytearray)) else out
        if errcode == 0:
            try:
                vDict = json.loads(out)
            except Exception:
                vDict = None
            if vDict:
                if vDict.get('is_live') != True:
                    return out, None, err, 999        #mean this is not a live
                title = vDict.get('uploader', '') + '_' + vDict.get('title', '')
                url = vDict.get('url', '')
                if url.endswith('.m3u8'):
                    return url, title, err, errcode
        else:
            tmp_retryTime += 1
            time.sleep(30)

    utitls.myLogger("_getYoutube_m3u8_sync SOURCE:{} ERROR:{}".format(youtubeLink, out))
    return out, None, err, errcode

def resolveStreamToM3u8(streamLink, isLog=True):
    out, title, err, errcode = None, streamLink, None, -1

    tmp_retryTime = 0
    while tmp_retryTime < 2:
        out, err, errcode = __runCMDSync('streamlink -j "{}" best'.format(streamLink), isLog)
        out = out.decode('utf-8') if isinstance(out, (bytes, bytearray)) else out
        if errcode == 0:
            try:
                vDict = json.loads(out)
            except Exception:
                vDict = None
            if vDict:
                streamM3U8 = vDict.get('url', None)
                if streamM3U8 == None:
                    return out, title, err, 999        #mean this is not a live

                tmp_title = streamLink
                tmp_uploader = ""

                # just pack the title
                videoId = streamLink.partition('/watch?v=')[2]
                if 'youtu.be/' in streamLink:
                    videoId = streamLink.partition('youtu.be/')[2]
                    videoId = videoId.split('/')[0]

                c_l = re.findall(r"channel/(.*)/live", streamLink)
                if len(c_l) > 0:    # find the channelID
                    channelID = c_l[0]
                    item = myRequests.getYoutubeLiveVideoInfoFromChannelID(channelID)
                    if item:
                        snippet = item.get('snippet', {})
                        tmp_title = snippet.get('title', streamLink)
                        tmp_uploader = snippet.get('channelTitle', channelID)
                elif videoId != '':
                    item = myRequests.getYoutubeLiveStreamInfo(videoId)
                    if item:
                        snippet = item.get('snippet', {})
                        tmp_title = snippet.get('title', streamLink)
                        tmp_uploader = snippet.get('channelTitle', "")

                title = "{}_{}".format(tmp_uploader, tmp_title)
                m3u8Link = streamLink
                return m3u8Link, title, err, errcode
        else:
            tmp_retryTime += 1
            time.sleep(30)

    if isLog:
        utitls.myLogger("resolveStreamToM3u8 SOURCE:{} ERROR:{}".format(streamLink, out))
    return out, title, err, errcode


def async_forwardStream(forwardLink, outputRTMP, isSubscribeQuest, subscribe_obj=None):
    utitls.runFuncAsyncThread(_forwardStream_sync, (forwardLink, outputRTMP, isSubscribeQuest, subscribe_obj))
def _forwardStream_sync(forwardLink, outputRTMP, isSubscribeQuest, subscribe_obj=None):
    tmp_quest = questInfo._getObjWithRTMPLink(outputRTMP)
    if tmp_quest:
        if tmp_quest.get('isRestart') == None:
            utitls.myLogger("_forwardStream_sync ERROR: rtmp already in quest!!!!\n forwardLink:%s, \n rtmpLink:%s" % (forwardLink, outputRTMP))
            return
    else:
        questInfo.addQuest(forwardLink, outputRTMP, isSubscribeQuest)

    if outputRTMP.startswith('rtmp://'):
        is_stream_playable = False

        tmp_title = forwardLink    # default title is the forwardLink
        tmp_forwardLink = forwardLink
        if 'twitcasting.tv/' in tmp_forwardLink:
            #('https://www.', 'twitcasting.tv/', 're2_takatsuki/fwer/aeqwet')
            tmp_twitcasID = tmp_forwardLink.partition('twitcasting.tv/')[2]
            tmp_twitcasID = tmp_twitcasID.split('/')[0]
            # if using the streamlink, it should be start with hlsvariant://
            tmp_forwardLink = 'hlsvariant://twitcasting.tv/{}/metastream.m3u8/?video=1'.format(tmp_twitcasID)
            is_stream_playable = True
        else:
            m3u8Link, tmp_title, err, errcode = resolveStreamToM3u8(tmp_forwardLink)
            tmp_forwardLink = forwardLink   # use the orgin streamlink
            if errcode == 0:
                is_stream_playable = True
            else:
                utitls.myLogger("_forwardStream_sync ERROR: Unsupport forwardLink:%s" % tmp_forwardLink)
                is_stream_playable = False

        if is_stream_playable == True:
            questInfo.updateQuestInfo('title', tmp_title, outputRTMP)
            if subscribe_obj:
                questInfo.updateQuestInfo('AccountMARK', subscribe_obj.get("mark", ""), outputRTMP)
                questInfo.updateQuestInfo('Live_URL', subscribe_obj.get("cur_blive_url", ""), outputRTMP)
            tmp_retryTime = 0
            tmp_cmdStartTime = time.time()
            while tmp_retryTime <= 2:  # must be <=
                # try to restream
                out, err, errcode = _forwardStreamCMD_sync(tmp_title, subscribe_obj, tmp_forwardLink, outputRTMP)

                out = out.decode('utf-8') if isinstance(out, (bytes, bytearray)) else out
                if '[cli][info] Stream ended' in out:           # this will cause the retry out, it good as so far.
                    utitls.myLogger("_forwardStreamCMD_sync LOG: Stream ended=======<")
                    break

                isQuestDead = questInfo._getObjWithRTMPLink(outputRTMP).get('isDead', False)
                if errcode == -9 or isQuestDead or isQuestDead == 'True':
                    utitls.myLogger("_forwardStreamCMD_sync LOG: Kill Current procces by rtmp:%s" % outputRTMP)
                    break
                # maybe can ignore the error if ran after 2min?
                if time.time() - tmp_cmdStartTime < 120:
                    tmp_retryTime += 1      # make it can exit
                else:
                    tmp_retryTime = 0      # let every Connect success reset the retrytime
                time.sleep(30)   # one m3u8 can hold 20 secounds or less
                tmp_cmdStartTime = time.time()  #import should not miss it.
                utitls.myLogger('_forwardStream_sync LOG: CURRENT RETRY TIME:%s' % tmp_retryTime)
                utitls.myLogger("_forwardStream_sync LOG RETRYING___________THIS:\ninputM3U8:%s, \noutputRTMP:%s" % (forwardLink, outputRTMP))
    else:
        utitls.myLogger("_forwardStream_sync ERROR: Invalid outputRTMP:%s" % outputRTMP)

    questInfo.removeQuest(outputRTMP)

# https://judge2020.com/restreaming-a-m3u8-hls-stream-to-youtube-using-ffmpeg/
def _forwardStreamCMD_sync(title, subscribe_obj, inputStreamLink, outputRTMP):
    os.makedirs('Videos', exist_ok=True)
    utitls.myLogger("_forwardStream_sync LOG:%s, %s" % (inputStreamLink, outputRTMP))
    title = title.replace('https', '')
    title = title.replace('http', '')
    title = title.replace('hlsvariant', '')
    reserved_list = ['/', '\\', ':', '?', '%', '*', '|', '"', '.', ' ', '<', '>']
    for val in reserved_list:
        title = title.replace(val, '_')

    out, err, errcode = None, None, None
    recordFilePath = os.path.join(
        os.getcwd(),
        'Videos',
        utitls.remove_emoji(title.strip()) + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    ) + '.mp4'

    # tmp_input = 'ffmpeg -loglevel error -i "{}"'.format(inputStreamLink)
    tmp_input = 'streamlink --retry-streams 3 --retry-max 10 --retry-open 10 -O {} best|ffmpeg -loglevel error -i pipe:0'.format(inputStreamLink)
    tmp_out_rtmp = '-f flv "{}"'.format(outputRTMP)
    tmp_out_file = '-y -f flv "{}"'.format(recordFilePath)

    tmp_encode = '-vcodec copy -acodec aac -strict -2 -ac 2 -bsf:a aac_adtstoasc -flags +global_header'

    cmd_list = [
        tmp_input,
        tmp_encode,
        tmp_out_rtmp
    ]

    tmp_should_record = None
    if subscribe_obj:
        tmp_should_record = subscribe_obj.get('is_should_record', None)
    if tmp_should_record == None:
        if utitls.configJson().get('is_auto_record', False):
            tmp_should_record = True

    if tmp_should_record == True:
        cmd_list.append('-vcodec copy -acodec aac -strict -2 -ac 2 -bsf:a aac_adtstoasc')
        cmd_list.append(tmp_out_file)

    cmd = ''
    for val in cmd_list:
        cmd += val + ' '
    cmd = cmd.strip()   #strip the last ' '

    out, err, errcode = __runCMDSync(cmd)
    return out, err, errcode
