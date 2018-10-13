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
  var tmp_dummy_02 = '发送写数字1，不发送写数字0';
  alert("如果当前账号是正在直播的状态，开播会覆盖当前任务")
  var val = document.getElementById("SelectAcc").value;
  var bpwd = prompt("请输入转播账号{" + val + "}操作码", tmp_dummy_01);
  var is_send_dynamic = prompt("是否发送直播动态？发送写数字1，不发送写数字0", tmp_dummy_02);
  if ((bpwd && is_send_dynamic) && (bpwd != tmp_dummy_01 && is_send_dynamic != tmp_dummy_02)){
    var tb = document.getElementById("restreamRtmpLink");
    tb.value = "ACCMARK=" + val
                + "&" + "OPTC=" + bpwd
                + "&" + "SEND_DYNAMIC=" + is_send_dynamic;
    tb.setAttribute("onmousedown", 'return false;');
    tb.setAttribute("onselectstart", 'return false;');

    alert("注意：此种方式开播后，不要进入B站直播后面页面操作，否则会导致RTMP流中断，并且不能自动恢复！！")
  } else {
    document.getElementById("SelectAcc")[0].selected = 'selected';
  }

}

getManualJson();
