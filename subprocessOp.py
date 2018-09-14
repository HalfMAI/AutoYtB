import subprocess
import utitls


def __runCMDSync(cmd):
     p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT ,universal_newlines=True)
     for line in p.stdout:
         utitls.myLogger(line)
     out, err = p.communicate()
     errcode = p.returncode
     utitls.myLogger("\nCMD: {}\nOUT: {}\nERR: {}\nERRCODE: {}".format(cmd, out, err, errcode))
     return out, err, errcode


def _getYotube_m3u8_sync(youtubeLink):
    out, err, errcode = __runCMDSync('youtube-dl -g {} --no-check-certificate'.format(youtubeLink))
    out = out.decode('utf-8').strip('\n')
    if not out.endswith('.m3u8'):
        errcode = -1
        utitls.myLogger("getYotube_m3u8 ERROR:%s" % out)
    return out, err, errcode

__g_rtmpLink = []

def async_forwardStream(link, outputRTMP):
    utitls.runFuncAsyncProcess(_forwardStream_sync, (link, outputRTMP))
def _forwardStream_sync(link, outputRTMP):
    # if outputRTMP in __g_rtmpLink:
    #
    #     return
    utitls.myLogger("_forwardStream_sync LOG:%s, %s" % (link, outputRTMP))

    if link.endswith('.m3u8') or '.m3u8' in link:
        _forwardStreamCMD(link, outputRTMP)
        return
    if 'youtube.com/' in link or 'youtu.be/' in link:
        m3u8Link, err, errcode = _getYotube_m3u8_sync(link)
        if errcode == 0:
            _forwardStreamCMD(m3u8Link, outputRTMP)
    else:
        utitls.myLogger("_forwardStream_sync ERROR")

    __g_rtmpLink.remove(outputRTMP)


def _forwardStreamCMD(inputM3U8, outputRTMP):
    __runCMDSync('ffmpeg -i "{}" -vcodec copy -acodec aac -strict -2 -f flv "{}"'.format(inputM3U8, outputRTMP))
