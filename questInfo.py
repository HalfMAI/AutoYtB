import utitls
import json

K_QUEST_JSON_PATH = 'tmp_QuestList.json'

def initQuestList():
    _saveQuestList([])

def _getQuestList():
    ret = []
    try:
        with open(K_QUEST_JSON_PATH, 'r', encoding='utf-8') as f:
            ret = json.loads(f.read()).get('quest_list')
            return ret
    except FileNotFoundError:
        initQuestList()
    return ret

def _saveQuestList(questList):
    tmp_dict = {'quest_list': questList}
    with open(K_QUEST_JSON_PATH, 'w', encoding='utf-8') as wf:
        json.dump(tmp_dict, wf, indent=4, sort_keys=True)


def checkIfInQuest(rtmpLink, isSubscribeQuest=False):
    #TODO do something with isSubscribeQuest?
    if _getObjWithRTMPLink(rtmpLink):
        return True
    else:
        return False

def updateQuestInfo(key, value, rtmpLink):
    tmp_quest_list = _getQuestList()
    for quest in tmp_quest_list:
        if quest.get('rtmpLink', "").split('/')[-1] == str(rtmpLink).split('/')[-1]:
            quest[key] = value
            break
    _saveQuestList(tmp_quest_list)


def addQuest(forwardLinkOrign, rtmpLink, isSubscribeQuest=False):
    if checkIfInQuest(rtmpLink, isSubscribeQuest):
        return

    forwardLinkOrign = str(forwardLinkOrign)
    rtmpLink = str(rtmpLink)
    questDict = {
        'isDead': False,
        'forwardLinkOrign': forwardLinkOrign,
        'rtmpLink': rtmpLink,
        'isSubscribeQuest': isSubscribeQuest,
        'title': None
    }
    utitls.myLogger('AddQuest LOG:\n AddQuest QUEST:%s' % questDict)
    tmp_quest_list = _getQuestList()
    tmp_quest_list.append(questDict)
    utitls.myLogger('Current Quest List:\n,{}'.format(tmp_quest_list))
    _saveQuestList(tmp_quest_list)

def removeQuest(rtmpLink):
    tmp_quest_list = _getQuestList()
    for quest in tmp_quest_list:
        if quest.get('rtmpLink', "").split('/')[-1] == str(rtmpLink).split('/')[-1]:
            utitls.myLogger('RemoveQuest LOG:\n Removed QUEST:%s' % quest)
            tmp_quest_list.remove(quest)
            utitls.myLogger('Current Quest List:\n,{}'.format(tmp_quest_list))
            _saveQuestList(tmp_quest_list)
            return

def _getObjWithRTMPLink(rtmpLink):
    tmp_quest_list = _getQuestList()
    ret = None
    for quest in tmp_quest_list:
        # just check the key. Bilibili's rtmp will be different if rtmp link is got from different IP
        if quest.get('rtmpLink', "").split('/')[-1] == rtmpLink.split('/')[-1]:
            ret = quest
            break
    return ret


def getQuestListStr():
    ret = ''
    tmp_quest_list = getQuestList_AddStarts()
    for quest in tmp_quest_list:
        ret += '---------Quest Start------------\n'
        for k,v in quest.items():
            ret += '{}: {}\n'.format(k, v)
        ret += '---------Quest End--------------\n'
    return ret

def getQuestList_AddStarts():
    ret = []
    tmp_quest_list = _getQuestList()
    for quest in tmp_quest_list:
        questDict = quest
        questDict['rtmpLink'] = 'rtmp://********************' + quest.get('rtmpLink', "")[-8:]
        ret.append(questDict)
    return ret
