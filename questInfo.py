import utitls

__g_QuestList = []
def checkIfInQuest(rtmpLink):
    for item in __g_QuestList:
        if rtmpLink == item.get('rtmpLink'):
            utitls.myLogger("checkIfInQuest LOG: %s is already in quest" % rtmpLink)
            return True
    return False

def addQuest(forwardLinkOrign, rtmpLink):
    questDict = {
        'forwardLinkOrign': forwardLinkOrign,
        'rtmpLink': rtmpLink
    }
    utitls.myLogger('AddQuest LOG:\n AddQuest QUEST:%s' % questDict)
    __g_QuestList.append(questDict)

def removeQuest(rtmpLink):
    for item in __g_QuestList:
        if rtmpLink == item.get('rtmpLink'):
            utitls.myLogger('RemoveQuest LOG:\n Removed QUEST:%s' % item)
            __g_QuestList.remove(item)
            return

def getQuestListStr():
    ret = ''
    for item in __g_QuestList:
        ret += '-----\nforwardLinkOrign:{}\nrtmpLink:{};'.format(
            item.get('forwardLinkOrign'),
            'rtmp://*****' + item.get('forwardLinkOrign')[-15]
        )
    return ret
