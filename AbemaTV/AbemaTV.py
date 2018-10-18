from time import sleep
import requests
import re
import subprocess
import threading
import sys
import os

K_CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

K_MAIN_M3U8 = "Main.m3u8"
K_SUB_M3U8 = "Sub.m3u8"

K_CHANNEL_NAME = "ultra-games"

_g_IsUsingMainM3u8 = True
_g_split_mark = "#EXTM3U"

def runFuncAsyncThread(target_func, args):
    t = threading.Thread(target=target_func, args=args)
    t.start()

def refreshM3u8(channel_name, uri_path, is_run_forever=True):
    global _g_IsUsingMainM3u8
    global _g_split_mark
    while True:
        pl = requests.get("https://linear-abematv.akamaized.net/channel/{}/1080/playlist.m3u8".format(channel_name), timeout=20).text
        ticket_list = re.findall(r"abematv-license://(.*)", pl)
        if len(ticket_list) >=1:
            uri_path = "{}?ticket={}".format(uri_path, ticket_list[0])
            cur_pl = re.sub('URI=.*?\,', 'URI=\"{}\",'.format(uri_path), pl)
        else:
            cur_pl = pl
        next_pl = None

        tmp_cur_mark = None
        tmp_list = cur_pl.partition('#EXT-X-DISCONTINUITY\n')
        if tmp_list[2] != '':   # if has next m3u8
            # set the split mark as the *.ts name
            tmp_cur_mark = tmp_list[0].partition('#EXT-X-DISCONTINUITY\n')[0].split('\n')[-2]
            cur_pl = tmp_list[0] + '#EXT-X-ENDLIST'     # make current m3u8 end playing the old list
            next_pl = '#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:5\n' + tmp_list[2]     # make the new list
        else:
            tmp_cur_mark = "#EXTM3U"

        if _g_split_mark not in cur_pl:
            _g_IsUsingMainM3u8 = False if _g_IsUsingMainM3u8 else True

        if tmp_cur_mark != _g_split_mark:
            _g_split_mark = tmp_cur_mark


        if _g_IsUsingMainM3u8:
            curFile = K_MAIN_M3U8
            nextFile = K_SUB_M3U8
        else:
            curFile = K_SUB_M3U8
            nextFile = K_MAIN_M3U8

        with open(curFile, "w") as f:
            f.write(cur_pl)
        print('-CURRENT-{} m3u8:\n{}\n'.format(curFile, cur_pl))

        if next_pl: # write the next file
            with open(nextFile, "w") as f:
                f.write(next_pl)
            print('-NEXT-{} m3u8:\n{}\n'.format(nextFile, next_pl))

        if is_run_forever == False:
            return cur_pl

        sleep(10)   #the m3u8 has 4 segments, it can hold 20 secounds, Default is updated every 5 secounds

def runCMD(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    pid = p.pid
    out, err = p.communicate()
    errcode = p.returncode
    return pid, out, err, errcode

def startFFMPEG(cmd, m3u8):
    m3u8_file = m3u8
    while True:
        print("====\nUsing the m3u8 File. -->{}".format(m3u8_file))
        pid, out, err, errcode  = runCMD(cmd)
        if errcode == 0:
            # filp the File
            # m3u8_file = K_MAIN_M3U8 if m3u8_file == K_SUB_M3U8 else K_SUB_M3U8
            print("----\nChanging the m3u8 File. \nChanging File To===>{}".format(m3u8_file))
        else:
            print("CMD RUN END with PID:{}\nOUT: {}\nERR: {}\nERRCODE: {}".format(pid, out, err, errcode))
            print('RETRYING___________THIS: startFFMPEG')
            sleep(5)


def restreamFromYoutube(youtubeURL, rtmp_link):
    sleep(10)   #wait for the restream
    while True:
        pid, out, err, errcode = runCMD('youtube-dl -g {}'.format(youtubeURL))
        out = out.decode('utf-8') if isinstance(out, (bytes, bytearray)) else out
        if '.m3u8' in out:
            youtubeM3u8 = out.strip()
            youtubeReCmd = 'ffmpeg -loglevel error \
                            -re \
                            -i "{}" \
                            -vcodec copy -acodec aac -strict -2 -ac 2 -bsf:a aac_adtstoasc \
                            -f flv "{}"'.format(youtubeM3u8, rtmp_link)
            startFFMPEG(youtubeReCmd, youtubeM3u8)

        sleep(10)


from abematv_plu import AbemaTV
g_ab = AbemaTV()
g_ab.init_usertoken()

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global g_ab
        body = ""
        if self.path == '/playlist.m3u8':
            m3u8_str = refreshM3u8(K_CHANNEL_NAME, 'myfile.dat', False)
            body = m3u8_str.encode('utf-8')
        elif '/myfile.dat?' in self.path:
            params = parse_qs(urlsplit(self.path).query)
            ticket_list = params.get('ticket', None)
            if ticket_list and len(ticket_list)>0:
                ticket = str.encode(ticket_list[0])
                body = g_ab.get_videokey_from_ticket(ticket)
                print("CurrentKey:" + body)
        self.send_response(200)
        self.send_header('Content-type', 'application/x-mpegURL')
        self.send_header('Content-length', len(body))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    if os.path.exists(K_MAIN_M3U8):
        os.remove(K_MAIN_M3U8)
    if os.path.exists(K_SUB_M3U8):
        os.remove(K_SUB_M3U8)

    rtmp_link = 'test.mp4'
    if len(sys.argv) >= 2:
        K_CHANNEL_NAME = sys.argv[1]
        rtmp_link = sys.argv[2]

    is_restream = False
    if len(sys.argv) >= 4:
        youtubeURL = sys.argv[3]
        bilibili_rtmp = sys.argv[4]
        is_restream = True

    print('RUNNING with channel:{} to {}'.format(K_CHANNEL_NAME, rtmp_link))

    abematvM3u8 = 'http://localhost:10800/playlist.m3u8'
    abematvCmd = 'ffmpeg -loglevel error \
                    -re \
                    -protocol_whitelist file,http,https,tcp,tls,crypto -allowed_extensions ALL \
                    -i "{}" \
                    -vcodec copy -acodec aac -strict -2 -ac 2 -bsf:a aac_adtstoasc \
                    -f flv "{}"'.format(abematvM3u8, rtmp_link)
    runFuncAsyncThread(startFFMPEG, (abematvCmd, abematvM3u8))

    if is_restream:
        # run the restream
        runFuncAsyncThread(restreamFromYoutube, (youtubeURL, bilibili_rtmp))


    httpd = HTTPServer(('localhost', 10800), MyHandler)
    httpd.serve_forever()
