import subprocess
import time

import utitls
import questInfo

def __runCMDSync(cmd):
     p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
     # !!!!!!!!!!!!!!p.pid
     # for line in p.stdout:
     #     utitls.myLogger(line)
     out, err = p.communicate()
     errcode = p.returncode
     utitls.myLogger("\nCMD: {}\nOUT: {}\nERR: {}\nERRCODE: {}".format(cmd, out, err, errcode))
     return out, err, errcode


def _getYotube_m3u8_sync(youtubeLink):
    out, err, errcode = __runCMDSync('youtube-dl -g {} --no-check-certificate'.format(youtubeLink))
    out = out.decode('utf-8') if isinstance(out, (bytes, bytearray)) else out
    out = out.strip('\n').strip()
    if not out.endswith('.m3u8'):
        errcode = -1
        utitls.myLogger("_getYotube_m3u8_sync ERROR:%s" % out)
    return out, err, errcode

def async_forwardStream(link, outputRTMP):
    utitls.runFuncAsyncProcess(_forwardStream_sync, (link, outputRTMP))
def _forwardStream_sync(link, outputRTMP):
    if questInfo.checkIfInQuest(outputRTMP):
        utitls.myLogger("_forwardStream_sync ERROR: rtmp already in quest!!!!\n link:%s, \n rtmpLink:%s" % (link, outputRTMP))
        return
    if outputRTMP.startswith('rtmp://') == False:
        utitls.myLogger("_forwardStream_sync ERROR: Invalid outputRTMP:%s" % outputRTMP)
        return

    if 'youtube.com/' in link or 'youtu.be/' in link:
        m3u8Link, err, errcode = _getYotube_m3u8_sync(link)
        if errcode == 0:
            link = m3u8Link

    if link.endswith('.m3u8') or '.m3u8' in link:
        questInfo.addQuest(link, outputRTMP)
        _forwardStreamCMD_sync(link, outputRTMP)
        questInfo.removeQuest(outputRTMP)
    else:
        utitls.myLogger("_forwardStream_sync ERROR: Unsupport forwardLink:%s", link)


def _forwardStreamCMD_sync(inputM3U8, outputRTMP):
    utitls.myLogger("_forwardStream_sync LOG:%s, %s" % (inputM3U8, outputRTMP))
    out, err, errcode = None, None, None
    tmp_retryTime = 3
    tmp_cmdStartTime = time.time()
    while tmp_retryTime > 0:
        out, err, errcode = __runCMDSync('ffmpeg -i "{}" -vcodec copy -acodec aac -strict -2 -f flv "{}"'.format(inputM3U8, outputRTMP))
        # maybe can ignore the error if it when wrong after 60s?
        if time.time() - tmp_cmdStartTime < 60:
            tmp_retryTime -= 1   # make it can exit
            tmp_cmdStartTime = time.time()
        time.sleep(5)
        utitls.myLogger('_forwardStreamCMD_sync LOG: CURRENT RETRY TIME:%s' % tmp_retryTime)
        utitls.myLogger("_forwardStream_sync LOG RETRYING___________THIS:%s, %s" % (inputM3U8, outputRTMP))
    return out, err, errcode
