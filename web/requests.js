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
function _disableBtnWithId(id, time){
    tmp_btn = document.getElementById(id);
    if (tmp_btn) {
      tmp_btn.disabled = true;
      setTimeout(function(){document.getElementById(id).disabled = false;}, time);
    }
}
function _disableAllBtn() {
  _disableBtnWithId("requestReStreamBtn", 3000);
  _disableBtnWithId("requestQuestListBtn", 3000);
  _disableBtnWithId("requestKillQuestBtn", 3000);
  _disableBtnWithId("refreshBTitleBtn", 10000);
  _disableBtnWithId("sendDynamicBtn", 10000);
  _disableBtnWithId("requestRefreshRTMPBtn", 10000);
  _disableBtnWithId("requestKillBRTMPBtn", 10000);
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

function _selectAcc(cb) {
  alert("此操作需要较长时间,操作后请等待30秒左右");
  var options_list = document.getElementById('SelectAcc').options;
  var tmp_list = [];
  for (var i = 1; i < options_list.length; i++) {
    var option = {
      text: options_list[i].text,
      value: options_list[i].value
    };
    tmp_list.push(option);
  }
  bootbox.prompt({
    title: "请选择操作的账号",
    inputType: 'select',
    inputOptions: tmp_list,
    callback: function (acc) {
      if (acc == null) { return; }
      bootbox.prompt({
        title: "请输入操作码",
        value: getCookie(acc),
        callback: function(opt_code){
          if (opt_code != null) { setCookie(acc, opt_code); }
          cb(acc, opt_code);
        }
      });
    }
  });
}

function requestReStream() {
  _disableAllBtn();
  var tmp_forwardLink = document.getElementById("forwardLink").value;
  var tmp_restreamRtmpLink = document.getElementById("restreamRtmpLink").value;
  if (tmp_restreamRtmpLink != "" && tmp_forwardLink != "") {
    var tmp_requestURL = "../live_restream?forwardLink=" + encodeURIComponent(tmp_forwardLink) + "&restreamRtmpLink=" + encodeURIComponent(tmp_restreamRtmpLink);
    _requestWithURL(tmp_requestURL, function(res_json){
      var tmp_responseMessageElement = document.getElementById("responseMessage");
      tmp_responseMessageElement.innerHTML = "";
      tmp_responseMessageElement.innerHTML += "请求返回码（为0或者1时说明当前任务已经添加成功）：" + res_json.code + '\n';
      tmp_responseMessageElement.innerHTML += res_json.msg;
    })
  }
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
  bootbox.prompt({
    title:"请输入需要关闭的RTMP流",
    value:"rtmp://XXXXXXXXXXXXX",
    callback: function(tmp_restreamRtmpLink) {
      if (tmp_restreamRtmpLink == null || "rtmp://XXXXXXXXXXXXX" == tmp_restreamRtmpLink){ return; }
      _disableAllBtn();
      var tmp_requestURL = "../kill_quest?rtmpLink=" + encodeURIComponent(tmp_restreamRtmpLink);
      _requestWithURL(tmp_requestURL, function(res_json){
        var tmp_responseMessageElement = document.getElementById("responseMessage");
        tmp_responseMessageElement.innerHTML = JSON.stringify(res_json);
      });
    }
  });
}
function requestChangeBTitle(){
  _selectAcc(function(acc, opt_code){
    bootbox.prompt("正在操作{" + acc + "},请输入直播间标题。\n如果不需要更改，请点击“取消”", function(b_title){
      if (b_title == null) { return; }
      bootbox.confirm("是否确认更改为：" + b_title, function(ret){
        if (ret == false) { return; }
        _disableAllBtn();
        var tmp_requestURL = "../bilibili_opt?changeTitle=" + encodeURIComponent(b_title)
            + "&acc=" + encodeURIComponent(acc)
            + "&opt_code=" + encodeURIComponent(opt_code);
        _requestWithURL(tmp_requestURL, function(res_json){
          var tmp_responseMessageElement = document.getElementById("responseMessage");
          tmp_responseMessageElement.innerHTML = JSON.stringify(res_json);
        });
      });
    });
  });
}
function requestSendDynamic(){
  _selectAcc(function(acc, opt_code){
    bootbox.prompt("正在操作{" + acc + "},请输入发送的动态。\n如果不需要发送，请点击“取消”", function(tmp_dynamic){
      if (tmp_dynamic == null) { return; }
      bootbox.confirm("是否确认发送动态：" + tmp_dynamic, function(ret){
        if (ret == false) { return; }
        _disableAllBtn();
        var tmp_requestURL = "../bilibili_opt?sendDynamic=" + encodeURIComponent(tmp_dynamic)
            + "&acc=" + encodeURIComponent(acc)
            + "&opt_code=" + encodeURIComponent(opt_code);
        _requestWithURL(tmp_requestURL, function(res_json){
          var tmp_responseMessageElement = document.getElementById("responseMessage");
          tmp_responseMessageElement.innerHTML = JSON.stringify(res_json);
        });
      });
    });
  });
}
function requestRefreshRTMP(){
  _selectAcc(function(acc, opt_code){
    bootbox.confirm("是否确认刷新RTMP流？(以服务器的IP重新开播一次。只有在使用直播台开播了之后，不小心进行了b站直播后台才需要进行些操作。操作的人最好清楚这是在做什么)", function(ret){
      if (ret == false) { return; }
      _disableAllBtn();
      var tmp_requestURL = "../bilibili_opt?refreshRTMP=1"
          + "&acc=" + encodeURIComponent(acc)
          + "&opt_code=" + encodeURIComponent(opt_code);
      _requestWithURL(tmp_requestURL, function(res_json){
        var tmp_responseMessageElement = document.getElementById("responseMessage");
        tmp_responseMessageElement.innerHTML = JSON.stringify(res_json);
      });
    });
  });
}
function requestKillBRTMP() {
  _selectAcc(function(acc, opt_code){
    bootbox.confirm("是否确认关闭当前B站任务RTMP流？(关闭转播任务,设计用于撞车时切换转播源或者某些原因需要关闭转播任务))", function(ret){
      if (ret == false) { return; }
      _disableAllBtn();
      var tmp_requestURL = "../bilibili_opt?killRTMP=1"
          + "&acc=" + encodeURIComponent(acc)
          + "&opt_code=" + encodeURIComponent(opt_code);
      _requestWithURL(tmp_requestURL, function(res_json){
        var tmp_responseMessageElement = document.getElementById("responseMessage");
        tmp_responseMessageElement.innerHTML = JSON.stringify(res_json);
      });
    });
  });
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
  bootbox.prompt({
    title: "请输入转播源的备注名字",
    value: tmp_dummy_01,
    callback: function(tmp_srcNote) {
      if (tmp_srcNote == null || tmp_srcNote == tmp_dummy_01) {return;}
      bootbox.prompt({
        title: "请输入转播源的地址",
        value: tmp_dummy_02,
        callback: function(tmp_srcLink) {
          if (tmp_srcLink == null || tmp_srcLink == tmp_dummy_02) {return;}
          bootbox.confirm({
            title: "请确认添加信息是否正确",
            message: "<p style=\"white-space: pre\">备注名字：\n" + tmp_srcNote + "\n转播源的地址:\n" + tmp_srcLink + "</p>",
            callback: function(is_ok) {
              if (is_ok == false) {return;}
              _disableAllBtn();
              var tmp_requestURL = "../addRestreamSrc?srcNote=" + encodeURIComponent(tmp_srcNote) + "&srcLink=" + encodeURIComponent(tmp_srcLink);
              _requestWithURL(tmp_requestURL, function(res_json){
                location.reload();
              });
            }
          });
        }
      });
    }
  });
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
  alert("请牢记，开播后 ！一定不能！进入B站直播中心页面操作");
  alert("如果当前账号是正在直播的状态，开播会覆盖当前任务.\n(同来源且同直播间不会覆盖)");
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
  var is_send_dynamic = confirm("是否发送直播动态？");
  is_send_dynamic = is_send_dynamic ? "1" : "0";

  var dynamic_words = "开始直播了,转播中";
  if (is_send_dynamic == true){
    tmp_word = prompt("请输入动态内容,以\\n做分行\n例：'这是\\n分行'\n下面已经填入了默认内容,最终发送时会自动附带直播间地址。", dynamic_words);
    if (tmp_word != null) { dynamic_words = tmp_word; }
  }

  var is_record = confirm("是否同时进行录像？");
  is_record = is_record ? "1" : "0";

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

    alert("!!!!注意!!!!!!\n此种账号开播方式开播后！一定！不要进入B站直播中心页面操作！！\n");
    alert("如果必需进入B站直播管理页面操作，请先操作B站直播管理页面后再从这里开播。\n\n否则会导致RTMP流中断，导致新进直播间的人不能观看，并且不能断开和恢复！！！！！！！"
    + "\n\n如果需要关闭直播间请自动进入b站后台进行关闭.");
    alert("请牢记，开播后 ！一定不能！进入B站直播中心页面操作");
  } else {
    document.getElementById("SelectAcc")[0].selected = 'selected';
  }
}

getManualJson();
