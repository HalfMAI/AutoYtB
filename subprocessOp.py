import subprocess
import time
import traceback

import utitls
import questInfo

def __runCMDSync(cmd):
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pid = p.pid
        utitls.myLogger("CMD RUN START with PID:{}\nCMD: {}".format(pid, cmd))
        try:
            rtmpLink = cmd.split(' ')[-1].strip('"')
            if rtmpLink.startswith('rtmp://'):
                questInfo.updateQuestWithPID(pid, rtmpLink)
        except Exception: pass
        out, err = p.communicate()
        errcode = p.returncode
        utitls.myLogger("CMD RUN END with PID:{}\nCMD: {}\nOUT: {}\nERR: {}\nERRCODE: {}".format(pid, cmd, out, err, errcode))
    except Exception as e:
        out, err, errcode = None, e, -1
        utitls.myLogger(traceback.format_exc())
    return out, err, errcode


def _getYotube_m3u8_sync(youtubeLink):
    out, err, errcode = None, None, -1

    tmp_retryTime = 0
    while tmp_retryTime <= 6:  # must be <=
        out, err, errcode = __runCMDSync('youtube-dl --no-check-certificate -g {}'.format(youtubeLink))
        out = out.decode('utf-8') if isinstance(out, (bytes, bytearray)) else out
        out = out.strip('\n').strip()
        if out.endswith('.m3u8'):
            return out, err, errcode
        else:
            tmp_retryTime -= 1
            utitls.myLogger("_getYotube_m3u8_sync RETRYING___________THIS:%s" % youtubeLink)
            time.sleep(10)

    utitls.myLogger("_getYotube_m3u8_sync ERROR:%s" % out)
    return out, err, errcode


def async_forwardStream(link, outputRTMP, isSubscribeQuest):
    utitls.runFuncAsyncThread(_forwardStream_sync, (link, outputRTMP, isSubscribeQuest))
def _forwardStream_sync(link, outputRTMP, isSubscribeQuest):
    if questInfo.checkIfInQuest(outputRTMP, isSubscribeQuest):
        utitls.myLogger("_forwardStream_sync ERROR: rtmp already in quest!!!!\n link:%s, \n rtmpLink:%s" % (link, outputRTMP))
        return
    questInfo.addQuest(link, outputRTMP, isSubscribeQuest)

    if outputRTMP.startswith('rtmp://'):
        if 'youtube.com/' in link or 'youtu.be/' in link:
            m3u8Link, err, errcode = _getYotube_m3u8_sync(link)
            if errcode == 0:
                link = m3u8Link

        if link.endswith('.m3u8') or '.m3u8' in link:
            _forwardStreamCMD_sync(link, outputRTMP)
        else:
            utitls.myLogger("_forwardStream_sync ERROR: Unsupport forwardLink:%s" % link)
    else:
        utitls.myLogger("_forwardStream_sync ERROR: Invalid outputRTMP:%s" % outputRTMP)

    questInfo.removeQuest(outputRTMP)

# https://judge2020.com/restreaming-a-m3u8-hls-stream-to-youtube-using-ffmpeg/
def _forwardStreamCMD_sync(inputM3U8, outputRTMP):
    utitls.myLogger("_forwardStream_sync LOG:%s, %s" % (inputM3U8, outputRTMP))
    out, err, errcode = None, None, None
    tmp_retryTime = 0
    tmp_cmdStartTime = time.time()
    while tmp_retryTime <= 10:  # must be <=
        out, err, errcode = __runCMDSync('ffmpeg -loglevel error -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2 -i "{}" -vcodec copy -acodec aac -strict -2 -ar 44100 -ab 128k -ac 2 -bsf:a aac_adtstoasc -bufsize 3000k -flags +global_header -f flv "{}"'.format(inputM3U8, outputRTMP))
        if errcode == -9 or questInfo._getObjWithRTMPLink(outputRTMP)['isDead']:
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
