function setCookie(name,value,days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}
function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}
function _disableBtnWithId(id){
    tmp_btn = document.getElementById(id);
    if (tmp_btn) {
      tmp_btn.disabled = true;
      setTimeout(function(){document.getElementById(id).disabled = false;}, 3000);
    }
}
function _disableAllBtn() {
  _disableBtnWithId("requestReStreamBtn");
  _disableBtnWithId("requestQuestListBtn");
  _disableBtnWithId("requestKillQuestBtn");
  _disableBtnWithId("addRestreamSrcBtn");
  _disableBtnWithId("addRtmpDesBtn");
}
function _requestWithURL(url, res) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      res_json = JSON.parse(this.responseText);
      res(res_json);
    }
  };
  xhttp.open("GET", url, true);
  xhttp.send();
}

function requestReStream() {
  _disableAllBtn();
  var tmp_forwardLink = document.getElementById("forwardLink").value;
  var tmp_restreamRtmpLink = document.getElementById("restreamRtmpLink").value;
  var tmp_requestURL = "../live_restream?forwardLink=" + encodeURIComponent(tmp_forwardLink) + "&restreamRtmpLink=" + encodeURIComponent(tmp_restreamRtmpLink);
  _requestWithURL(tmp_requestURL, function(res_json){
    var tmp_responseMessageElement = document.getElementById("responseMessage");
    tmp_responseMessageElement.innerHTML = "";
    tmp_responseMessageElement.innerHTML += "请求返回码（为0或者1时说明当前任务已经添加成功）：" + res_json.code + '\n';
    tmp_responseMessageElement.innerHTML += res_json.msg;
  })
}
function requestQuestList() {
  _disableAllBtn();
  var tmp_requestURL = "../questlist";
  _requestWithURL(tmp_requestURL, function(res_json){
    var tmp_responseMessageElement = document.getElementById("responseMessage");
    var tmp_retStr = "任务列表为：\n";
    res_json.forEach(function(item){
      tmp_retStr += "------------------\n";
      for(var key in item) {
        tmp_retStr += key + " -> " + item[key] + '\n';
      }
    });
    tmp_responseMessageElement.innerHTML = tmp_retStr;
  })
}
function requestKillQuest() {
  var tmp_restreamRtmpLink = prompt("请输入需要关闭的RTMP流", "rtmp://XXXXXXXXXXXXX");
  if (tmp_restreamRtmpLink){
    _disableAllBtn();
    var tmp_requestURL = "../kill_quest?rtmpLink=" + encodeURIComponent(tmp_restreamRtmpLink);
    _requestWithURL(tmp_requestURL, function(res_json){
      var tmp_responseMessageElement = document.getElementById("responseMessage");
      tmp_responseMessageElement.innerHTML = JSON.stringify(res_json);
    });
  }
}

function getManualJson() {
  var tmp_requestURL = "../get_manual_json"
  _requestWithURL(tmp_requestURL, function(res_json){
    srcDict = res_json['src_dict']
    addList = res_json['acc_mark_list']
    var selectSrc = document.getElementById("SelectSrc");
    var selectDes = document.getElementById("SelectAcc");
    for(var key in srcDict) {
      var option = document.createElement("option");
      option.text = key;
      option.value = srcDict[key];
      selectSrc.add(option);
    }
    for(var i in addList) {
      var option = document.createElement("option");
      option.text = addList[i];
      option.value = addList[i];
      selectDes.add(option);
    }
  });
}

function addRestreamSrc(){
  var tmp_dummy_01 = "例：神乐mea_Youtube";
  var tmp_dummy_02 = "例：https://www.youtube.com/channel/XXX/live";
  var tmp_srcNote = prompt("请输入转播源的备注名字", tmp_dummy_01);
  var tmp_srcLink = prompt("请输入转播源的地址", tmp_dummy_02);
  if ((tmp_srcNote && tmp_srcLink) && (tmp_srcNote != tmp_dummy_01 && tmp_srcLink != tmp_dummy_02)){
    _disableAllBtn();
    var tmp_requestURL = "../addRestreamSrc?srcNote=" + encodeURIComponent(tmp_srcNote) + "&srcLink=" + encodeURIComponent(tmp_srcLink);
    _requestWithURL(tmp_requestURL, function(res_json){
      location.reload();
    });
  }
}

function onSelectSrc() {
  var val = document.getElementById("SelectSrc").value;
  document.getElementById("forwardLink").value = val;
}

function onSelectDes() {
  var val = document.getElementById("SelectDes").value;
  var tb = document.getElementById("restreamRtmpLink");
  tb.value = val;
  // tb.setAttribute("onmousedown", 'return false;');
  // tb.setAttribute("onselectstart", 'return false;');
}

function onSelectAcc() {
  var tmp_dummy_01 = '请输入操作码';
  alert("！！请注意！！\n如果当前账号是正在直播的状态，开播会覆盖当前任务.\n(同来源且同直播间不会覆盖)");
  var val = document.getElementById("SelectAcc").value;

  var tmp_last_opt = getCookie(val);
  if (tmp_last_opt != null) { tmp_dummy_01 = tmp_last_opt; }
  var bpwd = prompt("请输入转播账号{" + val + "}操作码\n(操作码会记录在本地浏览器中,点击'取消'中断后续操作)", tmp_dummy_01);
  if (bpwd == null) {
    document.getElementById("SelectAcc")[0].selected = 'selected';
    return;
  }
  setCookie(val, bpwd);

  var b_title = null;
  b_title = prompt("请输入直播间标题。\n如果不需要更改，请点击“取消”");
  var is_send_dynamic = prompt("是否发送直播动态？\n发送写数字1，不发送写数字0.\n(默认不发送)", "0");

  var dynamic_words = "开始直播了\n转播中\n";
  if (is_send_dynamic == '1'){
    tmp_word = prompt("请输入动态内容,以\\n做分行\n例：'这是\\n分行'\n下面已经填入了默认内容,最终发送时会自动附带直播间地址。", dynamic_words);
    if (tmp_word != null) { dynamic_words = tmp_word; }
  }

  var is_record = "0";
  tmp_record = prompt("是否同时进行录像？\n录像写数字1，不录像写数字0\n默认不录像", is_record);
  if (tmp_record != null) { is_record = tmp_record; }

  if ((bpwd) && (bpwd != '请输入操作码')){
    var tb = document.getElementById("restreamRtmpLink");
    tb.value = "ACCMARK=" + val
                + "&" + "OPTC=" + bpwd
                + "&" + "SEND_DYNAMIC=" + is_send_dynamic
                + "&" + "DYNAMIC_WORDS=" + dynamic_words
                + "&" + "IS_SHOULD_RECORD=" + is_record;
    if (b_title) {
      tb.value += "&" + "B_TITLE=" + b_title;
    }

    tb.setAttribute("onmousedown", 'return false;');
    tb.setAttribute("onselectstart", 'return false;');

    alert("注意：此种方式开播后，(尽量)不要进入B站直播后面页面操作，否则会导致RTMP流中断，并且不能自动恢复！！\n如果需要关闭直播间请自动进入b站后台进行关闭.")
  } else {
    document.getElementById("SelectAcc")[0].selected = 'selected';
  }

}

getManualJson();
