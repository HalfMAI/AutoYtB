import utitls
import json

K_QUEST_JSON_PATH = 'tmp_QuestList.json'

def initQuestList():
    _saveQuestList([])

def _getQuestList():
    ret = []
    with open(K_QUEST_JSON_PATH, 'r', encoding='utf-8') as f:
        ret = json.loads(f.read()).get('quest_list')
        return ret

def _saveQuestList(questList):
    tmp_dict = {'quest_list': questList}
    with open(K_QUEST_JSON_PATH, 'w', encoding='utf-8') as wf:
        json.dump(tmp_dict, wf, indent=4, sort_keys=True)


def checkIfInQuest(rtmpLink):
    if _getObjWithRTMPLink(rtmpLink):
        return True
    else:
        return False

def addQuest(forwardLinkOrign, rtmpLink):
    forwardLinkOrign = str(forwardLinkOrign)
    rtmpLink = str(rtmpLink)
    questDict = {
        'forwardLinkOrign': forwardLinkOrign,
        'rtmpLink': rtmpLink
    }
    utitls.myLogger('AddQuest LOG:\n AddQuest QUEST:%s' % questDict)
    tmp_quest_list = _getQuestList()
    tmp_quest_list.append(questDict)
    _saveQuestList(tmp_quest_list)

def removeQuest(rtmpLink):
    item = _getObjWithRTMPLink(rtmpLink)
    if item:
        utitls.myLogger('RemoveQuest LOG:\n Removed QUEST:%s' % item)
        tmp_quest_list = _getQuestList()
        print(tmp_quest_list, item)
        tmp_quest_list.remove(item)
        _saveQuestList(tmp_quest_list)

def _getObjWithRTMPLink(rtmpLink):
    tmp_quest_list = _getQuestList()
    ret = None
    for item in tmp_quest_list:
        if item.get('rtmpLink') == rtmpLink:
            ret = item
            break
    return ret


def getQuestListStr():
    ret = ''
    tmp_quest_list = _getQuestList()
    for item in tmp_quest_list:
        try:
            tmp_rtmpLink = item.get('rtmpLink', "")[-5:]
        except IndexError:
            tmp_rtmpLink = "XXXXXXXXX"
        ret += '--------\nforwardLinkOrign:{}\n--------rtmpLink:{};'.format(
            item.get('forwardLinkOrign', ""),
            'rtmp://*****' + tmp_rtmpLink
        )
    return ret
