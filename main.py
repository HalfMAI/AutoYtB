from http.server import HTTPServer
from socketserver import ThreadingMixIn
from requestHandler import RequestHandler
import AutoOperate
import utitls
import time
import traceback
import questInfo


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

def startWebServer():
    # ip = utitls.configJson().get('serverIP')
    port = utitls.configJson().get('serverPort')
    server = ThreadedHTTPServer(('', int(port)), RequestHandler)
    utitls.myLogger('WebServerStarted, Listening on localhost:%s' % port)
    # sys.stderr = open('logfile.txt', 'a+', 1)
    server.serve_forever()
    return server.shutdown()

def main():
    try:
        #init the quest list
        questInfo.initQuestList()
        startWebServer()

    except Exception as e:
        utitls.myLogger(traceback.format_exc())
        utitls.myLogger(str(e))

if __name__ == "__main__":
    AutoOperate.Async_subscribeTheList()
    try:
        while True:
            main()
            utitls.myLogger('RESTART WERSERVER')
            time.sleep(5)
    except KeyboardInterrupt:
        utitls.myLogger('Running END-------------------------\n')
