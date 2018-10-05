import os
import subprocess
import time, datetime
import json
import traceback

import utitls
import questInfo

def __runCMDSync(cmd):
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pid = p.pid
        utitls.myLogger("CMD RUN START with PID:{}\nCMD: {}".format(pid, cmd))
        try:
            rtmpLink = cmd.partition('-f flv "')[2].partition('"')[0]   #get the first -f link
            if rtmpLink.startswith('rtmp://'):
                questInfo.updateQuestInfo('pid', pid, rtmpLink)
        except Exception: pass
        out, err = p.communicate()
        errcode = p.returncode
        utitls.myLogger("CMD RUN END with PID:{}\nCMD: {}\nOUT: {}\nERR: {}\nERRCODE: {}".format(pid, cmd, out, err, errcode))
    except Exception as e:
        out, err, errcode = None, e, -1
        utitls.myLogger(traceback.format_exc())
    return out, err, errcode


def _getYoutube_m3u8_sync(youtubeLink):
    out, err, errcode = None, None, -1

    tmp_retryTime = 0
    while tmp_retryTime < 2:
        out, err, errcode = __runCMDSync('youtube-dl --no-check-certificate -j {}'.format(youtubeLink))
        out = out.decode('utf-8') if isinstance(out, (bytes, bytearray)) else out
        if errcode == 0:
            try:
                vDict = json.loads(out)
            except Exception:
                vDict = None
            if vDict:
                if vDict.get('is_live') != True:
                    return out, err, 999        #mean this is not a live
                title = vDict.get('uploader', '') + '_' + vDict.get('title', '')
                url = vDict.get('url', '')
                if url.endswith('.m3u8'):
                    return url, title, err, errcode
        else:
            tmp_retryTime += 1
            time.sleep(30)

    utitls.myLogger("_getYoutube_m3u8_sync ERROR:%s" % out)
    return out, None, err, errcode


def async_forwardStream(link, outputRTMP, isSubscribeQuest):
    utitls.runFuncAsyncThread(_forwardStream_sync, (link, outputRTMP, isSubscribeQuest))
def _forwardStream_sync(link, outputRTMP, isSubscribeQuest):
    if questInfo.checkIfInQuest(outputRTMP, isSubscribeQuest):
        utitls.myLogger("_forwardStream_sync ERROR: rtmp already in quest!!!!\n link:%s, \n rtmpLink:%s" % (link, outputRTMP))
        return
    questInfo.addQuest(link, outputRTMP, isSubscribeQuest)

    if outputRTMP.startswith('rtmp://'):
        title = link    # default title is the link
        if 'youtube.com/' in link or 'youtu.be/' in link:
            m3u8Link, title, err, errcode = _getYoutube_m3u8_sync(link)
            if errcode == 0:
                link = m3u8Link

        questInfo.updateQuestInfo('title', title, outputRTMP)
        if link.endswith('.m3u8') or '.m3u8' in link:
            _forwardStreamCMD_sync(title, link, outputRTMP)
        else:
            utitls.myLogger("_forwardStream_sync ERROR: Unsupport forwardLink:%s" % link)
    else:
        utitls.myLogger("_forwardStream_sync ERROR: Invalid outputRTMP:%s" % outputRTMP)

    questInfo.removeQuest(outputRTMP)

# https://judge2020.com/restreaming-a-m3u8-hls-stream-to-youtube-using-ffmpeg/
def _forwardStreamCMD_sync(title, inputM3U8, outputRTMP):
    os.makedirs('Videos', exist_ok=True)
    utitls.myLogger("_forwardStream_sync LOG:%s, %s" % (inputM3U8, outputRTMP))
    title = title.replace('/', '_')
    title = title.replace(':', '_')
    title = title.replace('https:', '')
    title = title.replace('http:', '')

    out, err, errcode = None, None, None
    tmp_retryTime = 0
    tmp_cmdStartTime = time.time()
    while tmp_retryTime <= 10:  # must be <=
        recordFilePath = os.path.join(
            os.getcwd(),
            'Videos',
            utitls.remove_emoji(title.strip()) + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        ) + '.mp4'
        out, err, errcode = __runCMDSync(
                'ffmpeg -loglevel error -i "{}" \
                -vcodec copy -acodec aac -strict -2 -ac 2 -bsf:a aac_adtstoasc -bufsize 3000k -flags +global_header \
                -f flv "{}" \
                -vcodec copy -acodec aac -strict -2 -ac 2 -bsf:a aac_adtstoasc -bufsize 3000k -flags +global_header \
                -y -f flv "{}" \
                '.format(
                    inputM3U8, outputRTMP, recordFilePath
            )
        )
        isQuestDead = questInfo._getObjWithRTMPLink(outputRTMP)['isDead']
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
