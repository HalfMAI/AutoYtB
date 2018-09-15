from http.server import HTTPServer
from requestHandler import RequestHandler
from myRequests import subscribe, unsubscribe
import utitls
import time
import sys
import traceback

def startWebServer():
    # ip = utitls.configJson().get('serverIP')
    port = utitls.configJson().get('serverPort')
    server = HTTPServer(('', int(port)), RequestHandler)
    utitls.myLogger('WebServerStarted, Listening on localhost:%s' % port)
    sys.stderr = open('logfile.txt', 'a+', 1)
    server.serve_forever()
    return server.shutdown()


def Async_subscribeTheList(isSubscribe):
    utitls.runFuncAsyncProcess(subscribeTheList_sync, (isSubscribe,))
def subscribeTheList_sync(isSubscribe):
    subscribeList = utitls.configJson().get('subscribeList')
    ip = utitls.configJson().get('serverIP')
    for item in subscribeList:
        tmp_subscribeId = item.get('youtubeChannelId', "")
        if tmp_subscribeId != "":
            tmp_callback_url = 'http://' + ip + '/subscribe'
            if isSubscribe:
                time.sleep(5)   #wait the server starting up
                subscribe(tmp_callback_url, tmp_subscribeId)
            else:
                unsubscribe(tmp_callback_url, tmp_subscribeId)



def main():
    try:
        Async_subscribeTheList(True)
        startWebServer()
        subscribeTheList_sync(False)

    except Exception as e:
        subscribeTheList_sync(False)
        utitls.myLogger(traceback.format_exc())
        utitls.myLogger(str(e))

if __name__ == "__main__":
    try:
        while True:
            main()
            utitls.myLogger('RESTART WERSERVER')
            time.sleep(5)
    except KeyboardInterrupt:
        subscribeTheList_sync(False)
        utitls.myLogger('Running END-------------------------\n')
