const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const themeNames = { obsidian: "曜石黑", cloud: "云境白", oriental: "东方绛" };

const state = {
  ratio: "9:16",
  duration: 5,
  quality: "fast",
  resolution: "720p",
  generateAudio: false,
  taskId: null,
  pollTimer: null,
  assetObjectUrl: null,
  credits: 0,
  usedCredits: 0,
  monthlyLimit: 0,
  reservedCredits: 0,
  usage: null,
  works: []
};

const elements = {
  form: $("#generation-form"),
  prompt: $("#prompt-input"),
  charCount: $("#char-count"),
  formError: $("#form-error"),
  generateButton: $("#generate-button"),
  enhanceButton: $("#enhance-button"),
  estimateCredit: $("#estimate-credit"),
  estimateTime: $("#estimate-time"),
  costHint: $("#cost-hint"),
  audioToggle: $("#audio-toggle"),
  creditValue: $("#credit-value"),
  usedCredit: $("#used-credit"),
  creditLimit: $("#credit-limit"),
  usageTrack: $("#usage-track"),
  usageBar: $("#usage-bar"),
  previewEmpty: $("#preview-empty"),
  previewLoading: $("#preview-loading"),
  previewFailure: $("#preview-failure"),
  previewResult: $("#preview-result"),
  progressTrack: $("#progress-track"),
  progressBar: $("#progress-bar"),
  progressCopy: $("#progress-copy"),
  stageLabel: $("#stage-label"),
  stageDescription: $("#stage-description"),
  resultVideo: $("#result-video"),
  previewStage: $("#preview-stage"),
  outputSpec: $("#output-spec"),
  modelLabel: $(".model-label"),
  cancelButton: $("#cancel-button"),
  toast: $("#toast"),
  failureTitle: $("#failure-title"),
  failureMessage: $("#failure-message"),
  failureAction: $("#failure-action"),
  dialog: $("#app-dialog"),
  dialogKicker: $("#dialog-kicker"),
  dialogTitle: $("#dialog-title"),
  dialogContent: $("#dialog-content")
};

const panelContent = {
  credits: {
    kicker: "USAGE",
    title: "创作额度",
    render: () => `
      <p class="dialog-lead">额度由 Python 服务统一管理。任务提交时预留，生成成功后结算，失败或取消时自动释放。</p>
      <div class="info-grid">
        <div class="info-card"><span>当前可用</span><strong>${state.credits} 额度</strong><p>视频成功生成后才扣除本地额度。</p></div>
        <div class="info-card"><span>本月已使用</span><strong>${state.usedCredits} / ${state.monthlyLimit}</strong><p>另有 ${state.reservedCredits} 额度正在生成任务中预留。</p></div>
      </div>
      <div class="dialog-actions"><button class="dialog-action" type="button" data-open-panel="billing">查看套餐</button></div>`
  },
  templates: {
    kicker: "PROMPT LIBRARY",
    title: "灵感模板",
    render: () => `
      <p class="dialog-lead">选择一个成熟的镜头结构，它会自动填入创作描述，你仍可继续修改。</p>
      <div class="template-grid">
        <button class="template-card" type="button" data-template-prompt="清晨的海边公路，一辆银色跑车沿海岸线飞驰，低机位跟拍，阳光穿过薄雾，电影广告质感。"><strong>汽车广告</strong><span>低机位跟拍、自然光与商业电影质感。</span></button>
        <button class="template-card" type="button" data-template-prompt="一只橘猫坐在宇宙飞船驾驶舱里穿越星云，镜头从侧面缓慢环绕，画面精致有趣，动画电影风格。"><strong>奇幻想象</strong><span>角色叙事、环绕镜头与动画电影风格。</span></button>
        <button class="template-card" type="button" data-template-prompt="黑色岩石上的透明香水瓶，水流从瓶身两侧穿过，冷调柔光，缓慢推进，奢华商业摄影风格。"><strong>产品大片</strong><span>材质特写、克制运镜与高级商业光影。</span></button>
        <button class="template-card" type="button" data-template-prompt="雨后的江南庭院，青石板映着微光，镜头穿过竹叶缓慢推进至白瓷茶盏，薄雾流动，东方电影美学。"><strong>东方意境</strong><span>空间层次、薄雾氛围与缓慢推进。</span></button>
      </div>`
  },
  assets: {
    kicker: "BRAND ASSETS",
    title: "品牌素材",
    render: () => `
      <p class="dialog-lead">选择本地图片进行预览和素材检查。当前文本生成接口不会上传该文件，后续接入图生视频时可复用此入口。</p>
      <label class="upload-zone" for="asset-input"><div><strong>选择品牌参考图</strong><p>支持 PNG、JPG、WEBP，单文件不超过 10 MB</p><span class="upload-button">选择文件</span></div><input id="asset-input" type="file" accept="image/png,image/jpeg,image/webp" /></label>
      <div id="asset-result"></div>`
  },
  billing: {
    kicker: "PLANS",
    title: "套餐与账单",
    render: () => `<div class="panel-loading">正在读取套餐和账单</div>`
  },
  help: {
    kicker: "SUPPORT",
    title: "使用帮助",
    render: () => `
      <p class="dialog-lead">从描述画面到下载成片，常见问题都可以在这里快速排查。</p>
      <div class="help-list">
        <div class="help-item"><strong>怎样提高生成质量？</strong><p>依次描述主体、环境、动作、镜头运动、光线与风格，避免互相冲突的要求。</p></div>
        <div class="help-item"><strong>为什么生成需要等待？</strong><p>视频任务由火山方舟异步处理，繁忙时会先进入队列，页面会持续同步状态。</p></div>
        <div class="help-item"><strong>失败会扣本地额度吗？</strong><p>不会。本地额度只在任务成功并返回视频后扣除，供应商账单以火山方舟为准。</p></div>
      </div>
      <div class="dialog-actions"><button class="dialog-action secondary" type="button" data-copy="http://127.0.0.1:4173">复制工作台地址</button></div>`
  },
  works: {
    kicker: "LIBRARY",
    title: "全部作品",
    render: () => `<div class="panel-loading">正在读取作品库</div>`
  }
};

function applyTheme(theme) {
  const next = themeNames[theme] ? theme : "obsidian";
  document.documentElement.dataset.theme = next;
  $("#theme-current").textContent = themeNames[next];
  $$('[data-theme-value]').forEach((button) => {
    button.setAttribute("aria-checked", String(button.dataset.themeValue === next));
  });
  localStorage.setItem("frameflow-theme", next);
}

function setThemeMenu(open, focusFirst = false) {
  const trigger = $("#theme-button");
  const menu = $("#theme-menu");
  trigger.setAttribute("aria-expanded", String(open));
  menu.hidden = !open;
  if (open && focusFirst) {
    const selected = menu.querySelector('[aria-checked="true"]');
    (selected || menu.querySelector("button"))?.focus();
  }
}

function updateCredits() {
  elements.creditValue.textContent = state.credits;
  elements.usedCredit.textContent = state.usedCredits;
  elements.creditLimit.textContent = state.monthlyLimit;
  const percentage = state.monthlyLimit ? Math.min(100, (state.usedCredits / state.monthlyLimit) * 100) : 0;
  elements.usageBar.style.width = `${percentage}%`;
  elements.usageTrack.setAttribute("aria-label", `本月已使用 ${state.usedCredits}，总额度 ${state.monthlyLimit}`);
}

function getInput() {
  return {
    prompt: elements.prompt.value.trim(),
    ratio: state.ratio,
    duration: state.duration,
    quality: state.quality,
    resolution: state.resolution,
    generateAudio: state.generateAudio
  };
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.error?.message || "请求失败，请稍后重试");
    error.code = payload.error?.code;
    throw error;
  }
  return payload;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"
  })[character]);
}

function formatDate(timestamp) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
  }).format(new Date(timestamp));
}

function applyUsage(usage) {
  state.usage = usage;
  state.credits = usage.availableCredits;
  state.usedCredits = usage.usedCredits;
  state.monthlyLimit = usage.monthlyLimit;
  state.reservedCredits = usage.reservedCredits;
  updateCredits();
}

async function loadUsage() {
  const usage = await api("/api/account/usage");
  applyUsage(usage);
  return usage;
}

function workCard(work, index) {
  const card = document.createElement("article");
  card.className = `work-card ${["work-cosmetic", "work-auto", "work-space"][index % 3]}`;
  card.dataset.taskId = work.id;
  const preview = document.createElement("div");
  preview.className = "work-preview";
  const duration = document.createElement("span");
  duration.className = "duration-label";
  duration.textContent = `00:${String(work.duration).padStart(2, "0")}`;
  const play = document.createElement("button");
  play.type = "button";
  play.textContent = "播放";
  play.dataset.workTitle = work.title;
  play.dataset.workRatio = work.ratio;
  play.dataset.workUrl = work.resultUrl;
  play.setAttribute("aria-label", `播放${work.title}预览`);
  preview.append(duration, play);
  const copy = document.createElement("div");
  copy.className = "work-copy";
  const details = document.createElement("div");
  const title = document.createElement("h3");
  title.textContent = work.title;
  const meta = document.createElement("p");
  meta.textContent = `${formatDate(work.createdAt)} · ${work.ratio} · ${work.resolution}`;
  details.append(title, meta);
  const actions = document.createElement("div");
  actions.className = "work-actions";
  const status = document.createElement("span");
  status.className = "success-label";
  status.textContent = "已完成";
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "work-delete";
  remove.dataset.deleteWork = work.id;
  remove.setAttribute("aria-label", `从作品库删除${work.title}`);
  remove.textContent = "删除";
  actions.append(status, remove);
  copy.append(details, actions);
  card.append(preview, copy);
  return card;
}

function renderWorks() {
  const grid = $("#works-grid");
  grid.innerHTML = "";
  if (!state.works.length) {
    grid.innerHTML = `<div class="works-empty"><strong>还没有已完成作品</strong><p>视频成功生成后会自动进入作品库，并保留下载地址和创作参数。</p><button type="button" data-start-creation>开始第一支创作</button></div>`;
  } else {
    state.works.slice(0, 6).forEach((work, index) => grid.append(workCard(work, index)));
  }
  $("#work-count").textContent = String(state.works.length);
}

async function loadWorks() {
  const payload = await api("/api/works");
  state.works = payload.works;
  renderWorks();
  return state.works;
}

function renderWorksPanel() {
  if (!state.works.length) {
    elements.dialogContent.innerHTML = `<div class="works-empty panel-empty"><strong>作品库为空</strong><p>完成一次真实视频生成后，作品会自动保存在这里。</p><button type="button" data-start-creation>开始创作</button></div>`;
    return;
  }
  elements.dialogContent.innerHTML = `
    <p class="dialog-lead">这里仅展示真实生成成功的作品。可以播放、下载，或从本地作品库移除记录。</p>
    <div class="library-list">${state.works.map((work) => `
      <article class="library-row">
        <button type="button" class="library-play" data-work-title="${escapeHtml(work.title)}" data-work-ratio="${escapeHtml(work.ratio)}" data-work-url="${escapeHtml(work.resultUrl)}">
          <strong>${escapeHtml(work.title)}</strong><span>${work.duration} 秒 · ${escapeHtml(work.ratio)} · ${escapeHtml(work.resolution)} · ${formatDate(work.createdAt)}</span>
        </button>
        <a href="${escapeHtml(work.resultUrl)}" download="${escapeHtml(work.title)}.mp4">下载</a>
        <button type="button" class="work-delete" data-delete-work="${escapeHtml(work.id)}">删除</button>
      </article>`).join("")}
    </div>`;
}

function renderBilling(billing) {
  applyUsage(billing);
  const currentPlan = billing.plan.id;
  const statusMap = { reserved: "生成中", charged: "已结算", released: "已释放" };
  elements.dialogContent.innerHTML = `
    <p class="dialog-lead">当前套餐为「${escapeHtml(billing.plan.name)}」。切换套餐会立即更新本地账户额度；正式上线时可将该接口替换为支付回调。</p>
    <div class="plan-grid">${billing.plans.map((plan) => `
      <div class="plan-card ${plan.id === currentPlan ? "recommended" : ""}">
        <span>${plan.id === currentPlan ? "当前套餐" : "可切换"}</span>
        <strong>${escapeHtml(plan.name)}</strong>
        <div class="plan-price">${plan.price ? `¥${plan.price}/月` : "免费"}</div>
        <p>每月 ${plan.monthlyCredits} 创作额度</p>
        <button class="dialog-action ${plan.id === currentPlan ? "secondary" : ""}" type="button" data-plan-id="${plan.id}" ${plan.id === currentPlan ? "disabled" : ""}>${plan.id === currentPlan ? "使用中" : "切换套餐"}</button>
      </div>`).join("")}</div>
    <section class="billing-records"><h3>本月生成账单</h3>${billing.records.length ? `
      <div class="record-list">${billing.records.map((record) => `
        <div><span><strong>${escapeHtml(record.title)}</strong><small>${formatDate(record.createdAt)} · ${statusMap[record.status] || record.status}</small></span><b>${record.status === "charged" ? "-" : ""}${record.credits}</b></div>`).join("")}</div>` : `<div class="record-empty">本月还没有生成账单</div>`}</section>
    <section class="billing-records"><h3>套餐操作记录</h3>${billing.events.length ? `
      <div class="record-list">${billing.events.map((event) => `
        <div><span><strong>${escapeHtml(event.description)}</strong><small>${formatDate(event.createdAt)}</small></span><b>变更</b></div>`).join("")}</div>` : `<div class="record-empty">还没有套餐变更记录</div>`}</section>
    <div class="dialog-actions"><a class="dialog-action secondary" href="https://console.volcengine.com/ark/pricing" target="_blank" rel="noopener noreferrer">核对火山方舟成本</a></div>`;
}

let estimateTimer;
async function refreshEstimate() {
  clearTimeout(estimateTimer);
  estimateTimer = setTimeout(async () => {
    const input = getInput();
    if (input.prompt.length < 4) {
      const qualityFactor = input.quality === "pro" ? 1.7 : input.quality === "fast" ? .72 : 1;
      const resolutionFactor = { "480p": .58, "720p": 1, "1080p": 1.8 }[input.resolution];
      const audioFactor = input.generateAudio ? 1.15 : 1;
      elements.estimateCredit.textContent = Math.ceil(input.duration * qualityFactor * resolutionFactor * audioFactor);
      elements.estimateTime.textContent = input.quality === "fast" ? 32 : input.quality === "pro" ? 75 : 48;
      elements.costHint.textContent = input.resolution === "480p" ? "最低成本" : input.resolution === "720p" ? "省钱推荐" : "高清高成本";
      return;
    }
    try {
      const estimate = await api("/api/generations/estimate", { method: "POST", body: JSON.stringify(input) });
      elements.estimateCredit.textContent = estimate.credits;
      elements.estimateTime.textContent = estimate.estimatedSeconds;
      elements.costHint.textContent = input.resolution === "480p" ? "最低成本" : input.resolution === "720p" ? "省钱推荐" : "高清高成本";
    } catch {
      // 预估失败不阻断输入，提交时会再次校验。
    }
  }, 220);
}

function showError(message) {
  elements.formError.textContent = message;
  elements.formError.hidden = false;
}

function clearError() {
  elements.formError.hidden = true;
  elements.formError.textContent = "";
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => { elements.toast.hidden = true; }, 2800);
}

async function openPanel(name) {
  if (name === "credits") {
    try { await loadUsage(); } catch { showToast("额度数据加载失败"); }
  }
  const panel = panelContent[name];
  if (!panel) return;
  elements.dialogKicker.textContent = panel.kicker;
  elements.dialogTitle.textContent = panel.title;
  elements.dialogContent.innerHTML = panel.render();
  if (!elements.dialog.open) elements.dialog.showModal();
  try {
    if (name === "billing") renderBilling(await api("/api/billing"));
    if (name === "works") {
      await loadWorks();
      renderWorksPanel();
    }
  } catch (error) {
    elements.dialogContent.innerHTML = `<div class="works-empty panel-empty"><strong>数据加载失败</strong><p>${escapeHtml(error.message)}</p></div>`;
  }
}

function chooseTemplate(prompt) {
  elements.prompt.value = prompt;
  elements.charCount.textContent = String(prompt.length);
  elements.dialog.close();
  document.querySelector("#create").scrollIntoView({ behavior: "smooth", block: "start" });
  elements.prompt.focus({ preventScroll: true });
  refreshEstimate();
  showToast("模板已填入，可以继续修改或直接生成");
}

function playWork(title, ratio, url) {
  if (!url) {
    showToast("该作品没有可用的视频地址");
    return;
  }
  stopPolling();
  state.taskId = null;
  elements.resultVideo.src = url;
  $("#download-button").href = url;
  $("#download-button").download = `${title || "frameflow-video"}.mp4`;
  elements.outputSpec.textContent = `${ratio || "9:16"} · 作品预览`;
  setPreview("result");
  if (elements.dialog.open) elements.dialog.close();
  elements.previewStage.scrollIntoView({ behavior: "smooth", block: "center" });
  elements.resultVideo.play().catch(() => {});
  showToast(`正在预览「${title}」`);
}

function addCompletedWork(task) {
  if (!task.resultUrl) return;
  loadWorks().catch(() => showToast("作品库刷新失败，请稍后重试"));
}

function setPreview(view) {
  elements.previewEmpty.hidden = view !== "empty";
  elements.previewLoading.hidden = view !== "loading";
  elements.previewFailure.hidden = view !== "failure";
  elements.previewResult.hidden = view !== "result";
}

function stopPolling() {
  if (state.pollTimer) window.clearTimeout(state.pollTimer);
  state.pollTimer = null;
}

function updateTask(task) {
  elements.stageLabel.textContent = task.stage;
  elements.progressCopy.textContent = task.status === "queued" ? "等待创作资源" : `已完成 ${task.progress}%`;
  elements.progressBar.style.width = `${task.progress}%`;
  elements.progressTrack.setAttribute("aria-valuenow", String(task.progress));
  elements.stageDescription.textContent = task.status === "post_processing"
    ? "正在完成视频编码与安全检查"
    : "Agent 正在规划并生成完整镜头";

  if (task.status === "succeeded") {
    stopPolling();
    setPreview("result");
    if (task.resultUrl) {
      elements.resultVideo.src = task.resultUrl;
      $("#download-button").href = task.resultUrl;
      $("#download-button").download = `frameflow-${task.id}.mp4`;
    }
    elements.resultVideo.play().catch(() => {});
    loadUsage().catch(() => showToast("额度刷新失败，请稍后查看"));
    addCompletedWork(task);
    elements.generateButton.disabled = false;
    elements.generateButton.querySelector(".button-label").textContent = "再次生成";
    showToast("视频已经生成，可以预览或下载");
    return;
  }

  if (task.status === "cancelled" || task.status === "failed") {
    stopPolling();
    elements.generateButton.disabled = false;
    elements.generateButton.querySelector(".button-label").textContent = "生成视频";
    if (task.status === "cancelled") {
      setPreview("empty");
      loadUsage().catch(() => {});
      showToast("任务已取消，预留额度已经释放");
    } else {
      setPreview("failure");
      elements.failureTitle.textContent = task.stage || "视频生成失败";
      elements.failureMessage.textContent = task.errorMessage || "视频供应商未能完成任务，请检查配置后重试。";
      elements.failureAction.hidden = !task.actionUrl;
      if (task.actionUrl) elements.failureAction.href = task.actionUrl;
      loadUsage().catch(() => {});
      showToast("视频供应商返回了失败原因，请按提示处理");
    }
  }
}

async function pollTask() {
  if (!state.taskId) return;
  try {
    const { task } = await api(`/api/generations/${state.taskId}`);
    updateTask(task);
    if (!["succeeded", "failed", "cancelled"].includes(task.status)) {
      state.pollTimer = window.setTimeout(pollTask, 900);
    }
  } catch (error) {
    elements.stageDescription.textContent = "状态同步暂时中断，正在自动重试";
    state.pollTimer = window.setTimeout(pollTask, 2200);
  }
}

async function submitGeneration(event) {
  event.preventDefault();
  clearError();
  const input = getInput();
  if (input.prompt.length < 4) {
    showError("请至少输入 4 个字符，让 Agent 理解你的画面。");
    elements.prompt.focus();
    return;
  }
  const expectedCost = Number(elements.estimateCredit.textContent);
  if (expectedCost > state.credits) {
    showError("当前创作额度不足，请调整时长或升级套餐。");
    return;
  }

  stopPolling();
  elements.generateButton.disabled = true;
  elements.generateButton.querySelector(".button-label").textContent = "正在提交";
  setPreview("loading");
  elements.progressBar.style.width = "4%";
  elements.stageLabel.textContent = "正在理解创作意图";
  elements.outputSpec.textContent = `${input.ratio} · ${input.duration} 秒 · ${input.resolution}`;

  try {
    const idempotencyKey = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;
    const { task } = await api("/api/generations", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(input)
    });
    state.taskId = task.id;
    updateTask(task);
    loadUsage().catch(() => {});
    if (!["succeeded", "failed", "cancelled"].includes(task.status)) {
      state.pollTimer = window.setTimeout(pollTask, 700);
    }
  } catch (error) {
    setPreview("empty");
    elements.generateButton.disabled = false;
    elements.generateButton.querySelector(".button-label").textContent = "生成视频";
    showError(error.message);
  }
}

async function enhancePrompt() {
  clearError();
  const input = getInput();
  if (input.prompt.length < 4) {
    showError("先写下一点创意，再让 Agent 帮你润色。");
    elements.prompt.focus();
    return;
  }
  elements.enhanceButton.disabled = true;
  elements.enhanceButton.textContent = "润色中";
  try {
    const { intent } = await api("/api/intent/parse", { method: "POST", body: JSON.stringify(input) });
    elements.prompt.value = intent.enhancedPrompt;
    elements.charCount.textContent = elements.prompt.value.length;
    showToast("已补充镜头稳定性和光影描述");
    refreshEstimate();
  } catch (error) {
    showError(error.message);
  } finally {
    elements.enhanceButton.disabled = false;
    elements.enhanceButton.textContent = "智能润色";
  }
}

function resetCreation() {
  stopPolling();
  state.taskId = null;
  elements.prompt.value = "";
  elements.charCount.textContent = "0";
  elements.resultVideo.pause();
  setPreview("empty");
  clearError();
  elements.generateButton.disabled = false;
  elements.generateButton.querySelector(".button-label").textContent = "生成视频";
  elements.prompt.focus();
}

function startCreationFromPanel() {
  if (elements.dialog.open) elements.dialog.close();
  document.querySelector("#create").scrollIntoView({ behavior: "smooth", block: "start" });
  elements.prompt.focus({ preventScroll: true });
}

async function deleteWork(workId, button) {
  if (button.dataset.confirming !== "true") {
    button.dataset.confirming = "true";
    button.textContent = "确认删除";
    window.setTimeout(() => {
      if (button.isConnected) {
        button.dataset.confirming = "false";
        button.textContent = "删除";
      }
    }, 3200);
    return;
  }
  button.disabled = true;
  try {
    await api(`/api/works/${encodeURIComponent(workId)}`, { method: "DELETE" });
    await loadWorks();
    if (elements.dialog.open && elements.dialogTitle.textContent === "全部作品") renderWorksPanel();
    showToast("作品记录已删除，供应商原文件不受影响");
  } catch (error) {
    button.disabled = false;
    showToast(error.message);
  }
}

$("#theme-button").addEventListener("click", () => {
  const open = $("#theme-button").getAttribute("aria-expanded") !== "true";
  setThemeMenu(open);
});
$("#theme-button").addEventListener("keydown", (event) => {
  if (["ArrowDown", "Enter", " "].includes(event.key)) {
    event.preventDefault();
    setThemeMenu(true, true);
  }
});
$("#theme-menu").addEventListener("click", (event) => {
  const option = event.target.closest("[data-theme-value]");
  if (!option) return;
  applyTheme(option.dataset.themeValue);
  setThemeMenu(false);
  $("#theme-button").focus();
});
$("#theme-menu").addEventListener("keydown", (event) => {
  const options = $$('[data-theme-value]');
  const index = options.indexOf(document.activeElement);
  if (event.key === "Escape") {
    setThemeMenu(false);
    $("#theme-button").focus();
  } else if (["ArrowDown", "ArrowUp"].includes(event.key)) {
    event.preventDefault();
    const direction = event.key === "ArrowDown" ? 1 : -1;
    options[(index + direction + options.length) % options.length].focus();
  }
});
document.addEventListener("click", (event) => {
  if (!event.target.closest(".theme-picker")) setThemeMenu(false);
});
$("#credit-button").addEventListener("click", () => openPanel("credits"));
$("#upgrade-button").addEventListener("click", () => openPanel("billing"));
$("#all-works-button").addEventListener("click", () => openPanel("works"));
$("#dialog-close").addEventListener("click", () => elements.dialog.close());
elements.dialog.addEventListener("click", (event) => {
  if (event.target === elements.dialog) elements.dialog.close();
});
elements.dialogContent.addEventListener("click", async (event) => {
  const startButton = event.target.closest("[data-start-creation]");
  if (startButton) {
    startCreationFromPanel();
    return;
  }
  const deleteButton = event.target.closest("[data-delete-work]");
  if (deleteButton) {
    await deleteWork(deleteButton.dataset.deleteWork, deleteButton);
    return;
  }
  const planButton = event.target.closest("[data-plan-id]");
  if (planButton && !planButton.disabled) {
    planButton.disabled = true;
    planButton.textContent = "正在切换";
    try {
      const billing = await api("/api/billing/plan", {
        method: "POST",
        body: JSON.stringify({ planId: planButton.dataset.planId })
      });
      renderBilling(billing);
      showToast(`已切换到${billing.plan.name}`);
    } catch (error) {
      planButton.disabled = false;
      planButton.textContent = "切换套餐";
      showToast(error.message);
    }
    return;
  }
  const template = event.target.closest("[data-template-prompt]");
  if (template) {
    chooseTemplate(template.dataset.templatePrompt);
    return;
  }
  const work = event.target.closest("[data-work-title]");
  if (work) {
    playWork(work.dataset.workTitle, work.dataset.workRatio, work.dataset.workUrl);
    return;
  }
  const nextPanel = event.target.closest("[data-open-panel]");
  if (nextPanel) {
    openPanel(nextPanel.dataset.openPanel);
    return;
  }
  const copyButton = event.target.closest("[data-copy]");
  if (copyButton) {
    try {
      await navigator.clipboard.writeText(copyButton.dataset.copy);
      copyButton.textContent = "已复制";
      showToast("工作台地址已复制");
    } catch {
      showToast("浏览器未授权剪贴板，请手动复制地址栏");
    }
  }
});
elements.dialogContent.addEventListener("change", (event) => {
  if (event.target.id !== "asset-input") return;
  const file = event.target.files?.[0];
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) {
    showToast("图片不能超过 10 MB");
    event.target.value = "";
    return;
  }
  if (state.assetObjectUrl) URL.revokeObjectURL(state.assetObjectUrl);
  state.assetObjectUrl = URL.createObjectURL(file);
  const result = $("#asset-result");
  result.innerHTML = "";
  const preview = document.createElement("div");
  preview.className = "asset-preview";
  const image = document.createElement("img");
  image.src = state.assetObjectUrl;
  image.alt = "已选择的品牌素材预览";
  const details = document.createElement("div");
  const name = document.createElement("strong");
  name.textContent = file.name;
  const size = document.createElement("span");
  size.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB · 当前会话已选择`;
  details.append(name, size);
  preview.append(image, details);
  result.append(preview);
  showToast("品牌素材已加载到当前会话");
});

$$('[data-panel]').forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    openPanel(link.dataset.panel);
  });
});

$$('.side-nav a[href^="#"]:not([data-panel])').forEach((link) => {
  link.addEventListener("click", () => {
    $$(".side-nav .nav-item").forEach((item) => item.classList.remove("active"));
    link.classList.add("active");
  });
});
elements.prompt.addEventListener("input", () => {
  elements.charCount.textContent = elements.prompt.value.length;
  clearError();
  refreshEstimate();
});
elements.form.addEventListener("submit", submitGeneration);
elements.enhanceButton.addEventListener("click", enhancePrompt);
$("#new-creation").addEventListener("click", resetCreation);
$("#retry-button").addEventListener("click", () => {
  setPreview("empty");
  clearError();
  elements.prompt.focus();
});
$("#variant-button").addEventListener("click", () => {
  setPreview("empty");
  elements.generateButton.querySelector(".button-label").textContent = "生成同款变体";
  elements.prompt.focus();
});
elements.cancelButton.addEventListener("click", async () => {
  if (!state.taskId) return;
  elements.cancelButton.disabled = true;
  try {
    const { task } = await api(`/api/generations/${state.taskId}/cancel`, { method: "POST" });
    updateTask(task);
  } catch (error) {
    showToast(error.message);
  } finally {
    elements.cancelButton.disabled = false;
  }
});

$$('[data-setting]').forEach((group) => {
  group.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-value]");
    if (!button) return;
    group.querySelectorAll("button").forEach((item) => item.classList.remove("selected"));
    button.classList.add("selected");
    const setting = group.dataset.setting;
    state[setting] = setting === "duration" ? Number(button.dataset.value) : button.dataset.value;
    if (setting === "resolution") {
      state.quality = state.resolution === "1080p" ? "standard" : "fast";
      elements.modelLabel.textContent = state.resolution === "1080p" ? "标准高清模型" : "Fast 省钱模型";
    }
    elements.outputSpec.textContent = `${state.ratio} · ${state.duration} 秒 · ${state.resolution}`;
    refreshEstimate();
  });
});

elements.audioToggle.addEventListener("change", () => {
  state.generateAudio = elements.audioToggle.checked;
  refreshEstimate();
  showToast(state.generateAudio ? "已开启同步声音，生成成本会增加" : "已关闭同步声音，将按无声视频生成");
});

$$('.idea-chip').forEach((button) => {
  button.addEventListener("click", () => {
    elements.prompt.value = button.dataset.prompt;
    elements.charCount.textContent = elements.prompt.value.length;
    elements.prompt.focus();
    refreshEstimate();
  });
});

$("#works-grid").addEventListener("click", (event) => {
  const startButton = event.target.closest("[data-start-creation]");
  if (startButton) {
    startCreationFromPanel();
    return;
  }
  const deleteButton = event.target.closest("[data-delete-work]");
  if (deleteButton) {
    deleteWork(deleteButton.dataset.deleteWork, deleteButton);
    return;
  }
  const button = event.target.closest("button[data-work-title]");
  if (!button) return;
  playWork(button.dataset.workTitle, button.dataset.workRatio, button.dataset.workUrl);
});

applyTheme(localStorage.getItem("frameflow-theme") || "obsidian");
refreshEstimate();
Promise.all([loadUsage(), loadWorks()]).catch(() => {
  showToast("业务数据加载失败，请确认 Python 服务状态");
});
