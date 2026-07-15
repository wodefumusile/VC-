# -*- coding: utf-8 -*-
"""Web UI - Single Page Application (V2.2.3)"""
WEB_PAGE_HTML = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公众号AI运营系统 v2.2.3</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f0f2f5;color:#333;min-height:100vh}
:root{--primary:#4f46e5;--primary-hover:#4338ca;--success:#16a34a;--warn:#f59e0b;--danger:#dc2626;--bg:#f0f2f5;--card:#fff;--border:#e5e7eb;--text:#374151;--text-light:#6b7280}
/* Toast */
.toast{position:fixed;top:20px;right:20px;padding:12px 24px;border-radius:10px;color:#fff;font-size:14px;z-index:9999;animation:slideIn .3s ease;box-shadow:0 4px 12px rgba(0,0,0,.15)}
.toast-ok{background:var(--success)}.toast-err{background:var(--danger)}.toast-warn{background:var(--warn)}
@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}
/* Layout */
.topbar{background:var(--primary);color:#fff;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 8px rgba(0,0,0,.1)}
.topbar h1{font-size:18px;font-weight:600}
.topbar .mode-badge{font-size:12px;padding:4px 12px;border-radius:20px;font-weight:500}
.mode-full{background:#dcfce7;color:#166534}.mode-text{background:#fef3c7;color:#92400e}
nav{background:var(--card);border-bottom:1px solid var(--border);padding:0 24px;display:flex;gap:0}
nav a{padding:14px 20px;text-decoration:none;color:var(--text-light);font-size:14px;border-bottom:2px solid transparent;cursor:pointer;transition:all .2s}
nav a:hover,nav a.active{color:var(--primary);border-bottom-color:var(--primary)}
main{max-width:900px;margin:24px auto;padding:0 16px}
.card{background:var(--card);border-radius:12px;padding:24px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.06);border:1px solid var(--border)}
.card h3{font-size:16px;margin-bottom:16px;color:#1f2937}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:13px;color:var(--text-light);margin-bottom:4px;font-weight:500}
.form-group input,.form-group select,.form-group textarea{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:8px;font-size:14px;transition:border .2s;background:#fafafa}
.form-group input:focus,.form-group select:focus{border-color:var(--primary);outline:none;background:#fff}
.form-row{display:flex;gap:12px;flex-wrap:wrap}
.form-row .form-group{flex:1;min-width:150px}
.btn{padding:10px 20px;border:none;border-radius:8px;font-size:14px;font-weight:500;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:6px}
.btn-primary{background:var(--primary);color:#fff}.btn-primary:hover{background:var(--primary-hover)}
.btn-outline{background:#fff;color:var(--primary);border:1px solid var(--primary)}.btn-outline:hover{background:#f0f0ff}
.btn-danger{background:var(--danger);color:#fff}.btn-sm{padding:6px 14px;font-size:13px}
.btn:disabled{opacity:.5;cursor:not-allowed}
.msg{padding:10px 16px;border-radius:8px;font-size:13px;margin-top:12px;display:none}
.msg-ok{background:#f0fdf4;color:var(--success);display:block}
.msg-err{background:#fef2f2;color:var(--danger);display:block}
/* Progress */
.progress-wrap{display:none;margin-top:16px}
.progress-bar{height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden}
.progress-fill{height:100%;background:var(--primary);width:0;transition:width .3s;border-radius:3px}
.progress-text{font-size:12px;color:var(--text-light);margin-top:6px}
/* Tags */
.tag{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:500;margin:2px}
.tag-score{background:#ede9fe;color:#7c3aed}
.tag-ok{background:#dcfce7;color:#166534}
/* Status badge */
.status-badge{display:inline-flex;align-items:center;gap:4px;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:500}
.sb-ok{background:#dcfce7;color:#166534}.sb-pending{background:#f3f4f6;color:#6b7280}.sb-err{background:#fef2f2;color:#dc2626}
/* Toggle switch */
.toggle{display:flex;align-items:center;gap:12px;font-size:14px;cursor:pointer;padding:8px 0}
.toggle input{display:none}
.toggle-slider{width:44px;height:24px;background:#d1d5db;border-radius:12px;position:relative;transition:background .3s}
.toggle-slider::after{content:"";position:absolute;width:20px;height:20px;background:#fff;border-radius:50%;top:2px;left:2px;transition:transform .3s}
.toggle input:checked+.toggle-slider{background:var(--primary)}
.toggle input:checked+.toggle-slider::after{transform:translateX(20px)}
/* Article preview */
.article-preview{max-height:400px;overflow-y:auto;padding:16px;background:#fafafa;border-radius:8px;border:1px solid var(--border);font-size:14px;line-height:1.8}
.article-preview img{max-width:100%;border-radius:8px}
/* Onboarding */
.onboarding-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;z-index:8888}
.onboarding-card{background:#fff;border-radius:16px;padding:36px;max-width:460px;width:90%;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.2)}
.onboarding-card h2{font-size:20px;margin-bottom:8px;color:#1f2937}
.onboarding-card p{color:var(--text-light);margin-bottom:20px;line-height:1.6;font-size:14px}
.onboarding-card .step-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#d1d5db;margin:0 3px}
.onboarding-card .step-dot.active{background:var(--primary);width:24px;border-radius:4px}
@media(max-width:640px){.form-row{flex-direction:column}nav a{padding:12px 14px;font-size:13px}}
</style>
</head>
<body>

<!-- Onboarding -->
<div id="onboarding" class="onboarding-overlay" style="display:none">
<div class="onboarding-card">
<div id="onStepNum" style="background:#ede9fe;color:#7c3aed;width:36px;height:36px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;margin-bottom:12px">1</div>
<h2 id="onTitle">欢迎使用公众号AI运营系统</h2>
<p id="onDesc">让我们用 3 分钟完成配置，开始你的第一篇 AI 文章。</p>
<div style="margin-bottom:16px"><span class="step-dot active" id="dot0"></span><span class="step-dot" id="dot1"></span><span class="step-dot" id="dot2"></span><span class="step-dot" id="dot3"></span></div>
<button class="btn btn-primary" onclick="onboardingNext()" id="onBtn">开始配置</button>
<button class="btn btn-outline btn-sm" onclick="skipOnboarding()" style="margin-top:8px;display:block;width:100%">跳过，我熟悉操作</button>
</div>
</div>

<!-- Top Bar -->
<div class="topbar">
<h1>🚀 公众号AI运营系统</h1>
<span class="mode-badge mode-text" id="modeBadge">🟡 纯文本模式</span>
</div>

<!-- Navigation -->
<nav>
<a class="active" onclick="showPage('create')" id="navCreate">✏️ 文章生成</a>
<a onclick="showPage('history')" id="navHistory">📋 任务记录</a>
<a onclick="showPage('config')" id="navConfig">⚙️ 系统配置</a>
</nav>

<main>

<!-- PAGE: Create -->
<div id="pageCreate">
<div class="card">
<h3>✏️ 创建文章</h3>
<div class="form-row">
<div class="form-group" style="flex:3"><label>文章主题</label><input type="text" id="topicInput" placeholder="输入你想写的主题，例如：AI对普通人工作的影响"></div>
<div class="form-group"><label>风格</label><select id="styleSelect"><option value="marketing">营销推广</option><option value="science">科普知识</option><option value="case_study">案例分析</option><option value="branding">品牌故事</option></select></div>
<div class="form-group"><label>长度</label><select id="lengthSelect"><option value="short">短文</option><option value="medium" selected>中篇</option><option value="long">长文</option></select></div>
</div>
<button class="btn btn-primary" id="btnGenerate" onclick="generateArticle()">🚀 一键生成并发布</button>
<div class="progress-wrap" id="progressWrap">
<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
<div class="progress-text"><span id="progressLabel">正在生成文章...</span></div>
</div>
<div class="msg" id="createMsg"></div>
</div>
</div>

<!-- PAGE: History -->
<div id="pageHistory" style="display:none">
<div class="card">
<h3>📋 任务记录</h3>
<button class="btn btn-outline btn-sm" onclick="loadHistory()">🔄 刷新</button>
<div id="historyList" style="margin-top:16px;font-size:14px;color:var(--text-light)">加载中...</div>
</div>
</div>

<!-- PAGE: Config -->
<div id="pageConfig" style="display:none">
<div class="card">
<h3>🔑 DeepSeek AI</h3>
<div class="form-row">
<div class="form-group" style="flex:3"><label>API Key</label><input type="password" id="cfgAiKey" placeholder="sk-..."></div>
<div class="form-group" style="max-width:140px"><label>状态</label><span class="status-badge sb-pending" id="aiStatus">⏳ 未测试</span></div>
</div>
<button class="btn btn-outline btn-sm" onclick="testAiKey()">🔍 测试连接</button>
<span style="font-size:12px;color:var(--text-light);margin-left:8px" id="aiTestMsg"></span>
</div>

<div class="card">
<h3>🎨 图片生成</h3>
<div class="form-row">
<div class="form-group" style="flex:3"><label>API Key（可留空）</label><input type="password" id="cfgImageKey" placeholder="留空则跳过图片生成"></div>
<div class="form-group" style="max-width:140px"><label>状态</label><span class="status-badge sb-pending" id="imgStatus">⏳ 未测试</span></div>
</div>
<button class="btn btn-outline btn-sm" onclick="testImageKey()">🔍 测试连接</button>
<span style="font-size:12px;color:var(--text-light);margin-left:8px" id="imgTestMsg"></span>
</div>

<div class="card">
<h3>📁 Obsidian 知识库</h3>
<div class="form-group"><label>Vault 路径（可留空）</label><input type="text" id="cfgObsPath" placeholder="留空则跳过知识库，如：D:\MyNotes"></div>
<div id="obsInfo" style="display:none;padding:10px 14px;background:#f0f4ff;border-radius:8px;font-size:13px;margin-top:8px">
<span id="obsFileCount">📊 文件: -</span>
<span style="margin-left:16px" id="obsCharCount">📝 字数: -</span>
</div>
<button class="btn btn-outline btn-sm" onclick="scanObsidian()">🔄 同步知识库</button>
<span style="font-size:12px;color:var(--text-light);margin-left:8px" id="obsScanMsg"></span>
</div>

<div class="card">
<h3>🔧 模块开关</h3>
<label class="toggle"><input type="checkbox" id="cfgEnableAi" checked onchange="updateModeBadge()"><span class="toggle-slider"></span>AI 生成</label>
<label class="toggle"><input type="checkbox" id="cfgEnableKnowledge" onchange="updateModeBadge()"><span class="toggle-slider"></span>知识库增强</label>
<label class="toggle"><input type="checkbox" id="cfgEnableImage" onchange="updateModeBadge()"><span class="toggle-slider"></span>图片生成</label>
<div style="margin-top:16px;display:flex;gap:12px">
<button class="btn btn-primary" onclick="saveConfig()">💾 保存配置</button>
<button class="btn btn-outline" onclick="loadConfigPage()">🔄 重新加载</button>
</div>
<div class="msg" id="configMsg"></div>
</div>
</div>

<!-- PAGE: Article Detail -->
<div id="pageArticle" style="display:none">
<div class="card">
<h3 id="detailTitle" style="font-size:20px">—</h3>
<div style="margin-top:8px">
<span class="tag tag-score" id="detailScore"></span>
<span class="tag tag-ok" id="detailStatus"></span>
</div>
<p style="color:var(--text-light);font-size:13px;margin:8px 0" id="detailSummary"></p>
</div>
<div class="card"><h3>📝 正文预览</h3><div class="article-preview" id="detailContent">加载中...</div></div>
<div style="display:flex;gap:10px;margin-top:12px">
<button class="btn btn-primary" onclick="copyArticleHTML()">📋 复制HTML</button>
<button class="btn btn-danger" onclick="publishArticle()">📤 发布到微信草稿</button>
<button class="btn btn-outline" onclick="showPage('history')">← 返回列表</button>
</div>
</div>

</main>

<!-- Toast -->
<div id="toast" class="toast" style="display:none"></div>

<script>
// ===== Global State =====
var currentPage = "create";
var currentArticleId = null;
var adminToken = "__ADMIN_TOKEN_PLACEHOLDER__";
var onboardingStep = 0;
var onboardingSteps = [
  {num:1, title:"欢迎", desc:"公众号AI运营系统可以帮你自动生成和发布公众号文章。<br>只需输入主题，AI 自动完成写作、配图、排版。"},
  {num:2, title:"配置 DeepSeek AI", desc:"请输入你的 DeepSeek API Key。<br>还没有？<a href='https://platform.deepseek.com' target='_blank'>点此免费注册</a>，新用户有免费额度。"},
  {num:3, title:"配置图片生成 (可选)", desc:"如果你有即梦/豆包图片 API Key，可以自动为文章配图。<br>没有的话可以跳过，不影响文章生成。"},
  {num:4, title:"开始使用", desc:"配置完成！现在可以输入文章主题，点击生成。<br>系统会自动调用 AI 写作、排版，并保存到微信草稿箱。"}
];

// ===== Init =====
window.onload = function() {
  if (!localStorage.getItem("onboardingDone")) {
    document.getElementById("onboarding").style.display = "flex";
  }
  loadModeIndicator();
};

// ===== Toast =====
function toast(msg, type) {
  var t = document.getElementById("toast");
  t.textContent = msg; t.className = "toast toast-" + (type||"ok"); t.style.display = "block";
  setTimeout(function(){t.style.display="none"}, 3000);
}

// ===== Navigation =====
function showPage(page) {
  currentPage = page;
  ["create","history","config","article"].forEach(function(p){
    document.getElementById("page"+p.charAt(0).toUpperCase()+p.slice(1)).style.display = p===page ? "block" : "none";
    var nav = document.getElementById("nav"+p.charAt(0).toUpperCase()+p.slice(1));
    if (nav) nav.className = p===page ? "active" : "";
  });
  if (page === "config") loadConfigPage();
  if (page === "history") loadHistory();
}

// ===== Mode Indicator =====
function loadModeIndicator() {
  fetch("/api/v2/config").then(r=>r.json()).then(function(d){
    var c = d.data;
    var badge = document.getElementById("modeBadge");
    if (c.enable_image && c.image_api_key) {
      badge.textContent = "🟢 AI完整模式 (含配图)";
      badge.className = "mode-badge mode-full";
    } else {
      badge.textContent = "🟡 纯文本模式 (无配图)";
      badge.className = "mode-badge mode-text";
    }
  }).catch(function(){});
}
function updateModeBadge() {
  var img = document.getElementById("cfgEnableImage").checked;
  var badge = document.getElementById("modeBadge");
  if (img) { badge.textContent = "🟢 AI完整模式 (含配图)"; badge.className = "mode-badge mode-full"; }
  else { badge.textContent = "🟡 纯文本模式 (无配图)"; badge.className = "mode-badge mode-text"; }
}

// ===== Article Generation =====
function generateArticle() {
  var topic = document.getElementById("topicInput").value.trim();
  if (!topic) { toast("请输入文章主题", "warn"); return; }
  var btn = document.getElementById("btnGenerate"); btn.disabled = true;
  document.getElementById("progressWrap").style.display = "block";
  document.getElementById("progressFill").style.width = "20%";
  document.getElementById("progressLabel").textContent = "正在生成...";
  
  fetch("/api/v2/pipeline/run", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      topic:topic,
      style:document.getElementById("styleSelect").value,
      length:document.getElementById("lengthSelect").value,
      author:"wgzxhhh",
      template:"knowledge"
    })
  }).then(function(r){
    if (!r.ok) return r.json().then(function(e){throw new Error(e.error?.message||"生成失败")});
    return r.json();
  }).then(function(d){
    document.getElementById("progressFill").style.width = "100%";
    document.getElementById("progressLabel").textContent = "✅ 完成!";
    btn.disabled = false;
    if (d.data && d.data.id) {
      currentArticleId = d.data.id;
      toast("文章生成成功!", "ok");
      setTimeout(function(){ showPage("article"); loadArticleDetail(d.data.id); }, 500);
    }
  }).catch(function(e){
    btn.disabled = false;
    document.getElementById("progressWrap").style.display = "none";
    toast(e.message, "err");
  });
}

function loadArticleDetail(id) {
  if (!id) id = currentArticleId;
  if (!id) return;
  fetch("/api/v2/articles/"+id).then(r=>r.json()).then(function(d){
    var a = d.data;
    document.getElementById("detailTitle").textContent = a.title || "无标题";
    document.getElementById("detailSummary").textContent = a.summary || "";
    document.getElementById("detailScore").textContent = "评分: " + (a.quality_score || "N/A");
    document.getElementById("detailStatus").textContent = a.status || "";
    document.getElementById("detailContent").innerHTML = a.content_html || a.content || "无内容";
  }).catch(function(e){ toast("加载详情失败", "err"); });
}

function copyArticleHTML() {
  var html = document.getElementById("detailContent").innerHTML;
  navigator.clipboard.writeText(html).then(function(){toast("HTML已复制到剪贴板")});
}

function publishArticle() {
  if (!currentArticleId) return;
  toast("正在发布到微信草稿...", "warn");
  fetch("/api/v2/pipeline/run", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({topic:document.getElementById("detailTitle").textContent, style:"marketing", length:"medium"})
  }).catch(function(){});
}

// ===== History =====
function loadHistory() {
  fetch("/api/v2/articles/none").then(r=>r.json()).then(function(){
    document.getElementById("historyList").innerHTML = "<p style='color:var(--text-light)'>暂无任务记录</p>";
  }).catch(function(){
    // Try v1 api
    fetch("/api/tasks?limit=50").then(r=>r.json()).then(function(d){
      var tasks = d.data || d.tasks || [];
      if (tasks.length === 0) { document.getElementById("historyList").innerHTML = "<p>暂无任务记录</p>"; return; }
      var html = tasks.map(function(t){
        return '<div style="padding:12px;border-bottom:1px solid var(--border);cursor:pointer" onclick="currentArticleId=\''+(t.id||t.task_id)+'\';showPage(\'article\');loadArticleDetail()">'+
          '<strong>'+(t.title||t.topic||"无标题")+'</strong>'+
          '<span style="float:right;color:var(--text-light);font-size:12px">'+(t.status||"")+'</span>'+
          '</div>';
      }).join("");
      document.getElementById("historyList").innerHTML = html;
    }).catch(function(){ document.getElementById("historyList").innerHTML = "<p>加载失败</p>"; });
  });
}

// ===== Config Page =====
function loadConfigPage() {
  fetch("/api/v2/config").then(r=>r.json()).then(function(d){
    var c = d.data;
    document.getElementById("cfgAiKey").value = c.ai_api_key || "";
    document.getElementById("cfgImageKey").value = c.image_api_key || "";
    document.getElementById("cfgObsPath").value = c.obsidian_path || "";
    document.getElementById("cfgEnableAi").checked = c.enable_ai_generate !== false;
    document.getElementById("cfgEnableKnowledge").checked = c.enable_knowledge === true;
    document.getElementById("cfgEnableImage").checked = c.enable_image === true;
    updateModeBadge();
  }).catch(function(e){ toast("加载配置失败", "err"); });
}

function testAiKey() {
  var key = document.getElementById("cfgAiKey").value.trim();
  if (!key) { toast("请先输入 API Key", "warn"); return; }
  document.getElementById("aiTestMsg").textContent = "测试中...";
  document.getElementById("aiStatus").className = "status-badge sb-pending";
  document.getElementById("aiStatus").textContent = "⏳ 测试中";
  
  fetch("/api/v2/config/test-ai-key", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({api_key:key})
  }).then(function(r){
    if (r.ok) return r.json();
    return r.json().then(function(e){throw new Error(e.error?.message||"连接失败")});
  }).then(function(d){
    if (d.data && d.data.status === "success") {
      document.getElementById("aiStatus").className = "status-badge sb-ok";
      document.getElementById("aiStatus").textContent = "✅ 有效";
      document.getElementById("aiTestMsg").textContent = "连接成功!";
    } else {
      document.getElementById("aiStatus").className = "status-badge sb-err";
      document.getElementById("aiStatus").textContent = "❌ 无效";
      document.getElementById("aiTestMsg").textContent = (d.data&&d.data.message)||"连接失败";
    }
  }).catch(function(e){
    document.getElementById("aiStatus").className = "status-badge sb-err";
    document.getElementById("aiStatus").textContent = "❌ 失败";
    document.getElementById("aiTestMsg").textContent = e.message;
  });
}

function testImageKey() {
  var key = document.getElementById("cfgImageKey").value.trim();
  if (!key) { toast("请先输入 API Key", "warn"); return; }
  document.getElementById("imgTestMsg").textContent = "测试中...";
  fetch("/api/v2/config/test-image-key", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({api_key:key})
  }).then(function(r){
    if (r.ok) return r.json();
    return r.json().then(function(e){throw new Error(e.error?.message||"连接失败")});
  }).then(function(d){
    if (d.data && d.data.status === "success") {
      document.getElementById("imgStatus").className = "status-badge sb-ok";
      document.getElementById("imgStatus").textContent = "✅ 有效";
      document.getElementById("imgTestMsg").textContent = "连接成功!";
    } else {
      document.getElementById("imgStatus").className = "status-badge sb-err";
      document.getElementById("imgStatus").textContent = "❌ 无效";
      document.getElementById("imgTestMsg").textContent = "连接失败";
    }
  }).catch(function(e){
    document.getElementById("imgStatus").className = "status-badge sb-err";
    document.getElementById("imgStatus").textContent = "❌ 失败";
    document.getElementById("imgTestMsg").textContent = e.message;
  });
}

function scanObsidian() {
  var path = document.getElementById("cfgObsPath").value.trim();
  if (!path) { toast("请先输入 Obsidian 路径", "warn"); return; }
  document.getElementById("obsScanMsg").textContent = "同步中...";
  // Save path first
  saveObsPath(path).then(function(){
    fetch("/api/v2/knowledge/scan").then(r=>r.json()).then(function(d){
      document.getElementById("obsInfo").style.display = "block";
      document.getElementById("obsFileCount").textContent = "📊 文件: " + (d.data?.total_files||0);
      document.getElementById("obsCharCount").textContent = "📝 字数: " + (d.data?.total_chars||0);
      document.getElementById("obsScanMsg").textContent = "同步完成!";
      toast("知识库同步完成", "ok");
    }).catch(function(e){
      document.getElementById("obsScanMsg").textContent = "同步失败";
      toast("知识库未启用或路径无效", "err");
    });
  });
}

function saveObsPath(path) {
  return fetch("/api/v2/config", {
    method:"POST", headers:{"Content-Type":"application/json","Authorization":"Bearer "+adminToken},
    body:JSON.stringify({obsidian_path:path, enable_ai:true, enable_knowledge:true, enable_image:true})
  });
}

function saveConfig() {
  var btn = event.target; btn.disabled = true;
  var body = {
    ai_api_key: document.getElementById("cfgAiKey").value.trim(),
    image_api_key: document.getElementById("cfgImageKey").value.trim(),
    obsidian_path: document.getElementById("cfgObsPath").value.trim(),
    enable_ai: document.getElementById("cfgEnableAi").checked,
    enable_knowledge: document.getElementById("cfgEnableKnowledge").checked,
    enable_image: document.getElementById("cfgEnableImage").checked
  };
  fetch("/api/v2/config", {
    method:"POST", headers:{"Content-Type":"application/json","Authorization":"Bearer "+adminToken},
    body:JSON.stringify(body)
  }).then(function(r){
    if (!r.ok) return r.json().then(function(e){throw new Error(e.error?.message||"保存失败")});
    return r.json();
  }).then(function(){
    var msg = document.getElementById("configMsg");
    msg.className = "msg msg-ok";
    msg.innerHTML = "✅ ✅ 配置已保存！已自动生效。";
    btn.disabled = false;
    updateModeBadge();
    toast("配置已保存", "ok");
  }).catch(function(e){
    var msg = document.getElementById("configMsg");
    msg.className = "msg msg-err";
    msg.textContent = "保存失败: " + e.message;
    btn.disabled = false;
  });
}

// ===== Onboarding =====
function onboardingNext() {
  onboardingStep++;
  if (onboardingStep >= onboardingSteps.length) { closeOnboarding(); return; }
  var s = onboardingSteps[onboardingStep];
  document.getElementById("onStepNum").textContent = s.num;
  document.getElementById("onTitle").textContent = s.title;
  document.getElementById("onDesc").innerHTML = s.desc;
  for (var i=0;i<4;i++) document.getElementById("dot"+i).className = "step-dot"+(i<=onboardingStep?" active":"");
  if (onboardingStep === 2) document.getElementById("onBtn").textContent = "下一步";
  if (onboardingStep === 3) document.getElementById("onBtn").textContent = "🎉 完成，进入系统";
}
function skipOnboarding() { closeOnboarding(); }
function closeOnboarding() {
  document.getElementById("onboarding").style.display = "none";
  localStorage.setItem("onboardingDone", "1");
}

// ===== Keyboard shortcut =====
document.addEventListener("keydown", function(e){ if (e.key==="Escape") closeOnboarding(); });
</script>
</body>
</html>
"""
