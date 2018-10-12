import os
import subprocess
import time, datetime
import json
import traceback

import utitls
import questInfo

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

    utitls.myLogger("_getYoutube_m3u8_sync ERROR:%s" % out)
    return out, None, err, errcode


def async_forwardStream(forwardLink, outputRTMP, isSubscribeQuest):
    utitls.runFuncAsyncThread(_forwardStream_sync, (forwardLink, outputRTMP, isSubscribeQuest))
def _forwardStream_sync(forwardLink, outputRTMP, isSubscribeQuest):
    tmp_quest = questInfo._getObjWithRTMPLink(outputRTMP)
    if tmp_quest:
        if tmp_quest.get('isRestart') == None:
            utitls.myLogger("_forwardStream_sync ERROR: rtmp already in quest!!!!\n forwardLink:%s, \n rtmpLink:%s" % (forwardLink, outputRTMP))
            return
    else:
        questInfo.addQuest(forwardLink, outputRTMP, isSubscribeQuest)

    if outputRTMP.startswith('rtmp://'):
        title = forwardLink    # default title is the forwardLink
        if 'youtube.com/' in forwardLink \
            or 'youtu.be/' in forwardLink \
            or 'twitch.tv/' in forwardLink \
            or 'showroom-live.com/' in forwardLink:
            m3u8Link, title, err, errcode = _getYoutube_m3u8_sync(forwardLink)
            if errcode == 0:
                forwardLink = m3u8Link
        elif 'twitcasting.tv/' in forwardLink:
            #('https://www.', 'twitcasting.tv/', 're2_takatsuki/fwer/aeqwet')
            tmp_twitcasID = forwardLink.partition('twitcasting.tv/')[2]
            tmp_twitcasID = tmp_twitcasID.split('/')[0]
            forwardLink = 'http://twitcasting.tv/{}/metastream.m3u8/?video=1'.format(tmp_twitcasID)

        questInfo.updateQuestInfo('title', title, outputRTMP)
        if forwardLink.endswith('.m3u8') or '.m3u8' in forwardLink:
            _forwardStreamCMD_sync(title, forwardLink, outputRTMP)
        else:
            utitls.myLogger("_forwardStream_sync ERROR: Unsupport forwardLink:%s" % forwardLink)
    else:
        utitls.myLogger("_forwardStream_sync ERROR: Invalid outputRTMP:%s" % outputRTMP)

    questInfo.removeQuest(outputRTMP)

# https://judge2020.com/restreaming-a-m3u8-hls-stream-to-youtube-using-ffmpeg/
def _forwardStreamCMD_sync(title, inputM3U8, outputRTMP):
    os.makedirs('Videos', exist_ok=True)
    utitls.myLogger("_forwardStream_sync LOG:%s, %s" % (inputM3U8, outputRTMP))
    title = title.replace('https', '')
    title = title.replace('http', '')
    reserved_list = ['/', '\\', ':', '?', '%', '*', '|', '"', '.', ' ', '<', '>']
    for val in reserved_list:
        title = title.replace(val, '_')

    out, err, errcode = None, None, None
    tmp_retryTime = 0
    tmp_cmdStartTime = time.time()
    while tmp_retryTime <= 10:  # must be <=
        recordFilePath = os.path.join(
            os.getcwd(),
            'Videos',
            utitls.remove_emoji(title.strip()) + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        ) + '.mp4'

        tmp_input = 'ffmpeg -loglevel error -i "{}"'.format(inputM3U8)
        tmp_out_rtmp = '-f flv "{}"'.format(outputRTMP)
        tmp_out_file = '-y -f flv "{}"'.format(recordFilePath)

        tmp_encode = '-vcodec copy -acodec aac -strict -2 -ac 2 -bsf:a aac_adtstoasc -flags +global_header'

        cmd_list = [
            tmp_input,
            tmp_encode,
            tmp_out_rtmp
        ]

        if utitls.configJson().get('is_auto_record', False):
            cmd_list.append(tmp_encode)
            cmd_list.append(tmp_out_file)

        cmd = ''
        for val in cmd_list:
            cmd += val + ' '
        cmd = cmd.strip()   #strip the last ' '

        out, err, errcode = __runCMDSync(cmd)

        isQuestDead = questInfo._getObjWithRTMPLink(outputRTMP).get('isDead', False)
        if errcode == -9 or isQuestDead or isQuestDead == 'True':
            utitls.myLogger("_forwardStreamCMD_sync LOG: Kill Current procces by rtmp:%s" % outputRTMP)
            break
        # maybe can ignore the error if ran after 2min?
        if time.time() - tmp_cmdStartTime < 120:
            tmp_retryTime += 1      # make it can exit
        else:
            tmp_retryTime = 0      # let every Connect success reset the retrytime
        tmp_cmdStartTime = time.time()  #import should not miss it.
        time.sleep(10)   #rtmp buffer can hold 3 secounds or less
        utitls.myLogger('_forwardStreamCMD_sync LOG: CURRENT RETRY TIME:%s' % tmp_retryTime)
        utitls.myLogger("_forwardStream_sync LOG RETRYING___________THIS:\ninputM3U8:%s, \noutputRTMP:%s" % (inputM3U8, outputRTMP))
    return out, err, errcode
