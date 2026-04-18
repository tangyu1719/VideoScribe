(() => {
  const mountEl = document.getElementById("app");
  const API_BASE = "";

  const renderFatal = (title, detail) => {
    if (!mountEl) return;
    mountEl.innerHTML = `
      <div style="padding:24px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Microsoft YaHei,sans-serif">
        <h2 style="margin:0 0 10px;color:#b91c1c">${title}</h2>
        <pre style="white-space:pre-wrap;background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px;padding:12px;color:#111827">${detail || ""}</pre>
        <p style="color:#475569">请按 Ctrl+F5 强制刷新，如果仍失败我会继续改成本地静态依赖方案。</p>
      </div>
    `;
  };

  if (!window.Vue) {
    renderFatal("Vue 加载失败", "window.Vue 未定义（可能是浏览器拦截了 CDN 资源）");
    return;
  }
  if (!window.ElementPlus) {
    renderFatal("Element Plus 加载失败", "window.ElementPlus 未定义（可能是浏览器拦截了 CDN 资源）");
    return;
  }

  const { createApp, ref, reactive, onMounted } = window.Vue;

  createApp({
  setup() {
    const activeMenu = ref("video");
    const showPromptEditor = ref(false);
    const loading = ref(false);

    const form = reactive({
      template: "default_video",
      url: "",
      linkType: "default_video",
      enableFeishu: true,
      titleRule: "",
      summaryHint: "",
      userPrompt: "",
    });

    const statusText = ref("任务状态：使用AI进行文本总结...");
    const queueText = ref("队列：0 个任务");
    const externalLog = ref("");
    const chainLog = ref("");

    const appendLog = (msg) => {
      const line = `[${new Date().toLocaleTimeString()}] ${msg}`;
      externalLog.value = `${line}\n${externalLog.value}`.slice(0, 20000);
    };

    const postJson = async (url, body) => {
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      return r.json();
    };

    const callGuiEvent = async (eventId, payload = {}) => {
      return postJson(`${API_BASE}/api/gui/${encodeURIComponent(eventId)}`, { payload });
    };

    const detectLinkType = () => {
      const u = (form.url || "").toLowerCase();
      if (u.includes("xiaohongshu")) form.linkType = "xiaohongshu";
      else if (u.includes("bilibili")) form.linkType = "bilibili";
      else form.linkType = "default_video";
      appendLog(`识别链接类型: ${form.linkType}`);
    };

    const startProcess = async () => {
      loading.value = true;
      try {
        const data = await callGuiEvent("run_selected_workflow", {
          url: form.url,
          link_type: form.linkType,
          user_prompt: form.userPrompt,
          enable_feishu: form.enableFeishu,
          title_rule: form.titleRule,
          summary_hint: form.summaryHint,
        });
        statusText.value = data.ok ? "任务状态：已启动，等待执行..." : `任务状态：启动失败（${data.error || "未知错误"}）`;
        queueText.value = data.ok ? "队列：已加入 1 个任务" : "队列：提交失败";
        chainLog.value = JSON.stringify(data, null, 2);
        appendLog(data.ok ? "开始处理：任务已提交" : `开始处理失败: ${data.error || "unknown"}`);
      } finally {
        loading.value = false;
      }
    };

    const batchImport = async () => {
      const data = await callGuiEvent("batch_import");
      chainLog.value = JSON.stringify(data, null, 2);
      appendLog(data.ok ? "批量导入已触发" : `批量导入失败: ${data.error || "unknown"}`);
    };

    const topTrace = async () => {
      const res = await fetch(`${API_BASE}/api/workflow/state`);
      const data = await res.json();
      chainLog.value = JSON.stringify(data, null, 2);
      appendLog("顶层追踪已刷新");
    };

    const rebuildIndex = async () => {
      const data = await postJson(`${API_BASE}/api/kb/rebuild-index`, {});
      chainLog.value = JSON.stringify(data, null, 2);
      appendLog(data.ok ? "重建索引完成" : `重建索引失败: ${data.error || "unknown"}`);
    };

    onMounted(async () => {
      await callGuiEvent("show_video_page");
      appendLog("页面已就绪（Vue + Element Plus）");
    });

    return {
      activeMenu,
      showPromptEditor,
      loading,
      form,
      statusText,
      queueText,
      externalLog,
      chainLog,
      detectLinkType,
      startProcess,
      batchImport,
      topTrace,
      rebuildIndex,
    };
  },
    template: `
    <el-container class="page-root">
      <el-aside width="220px" class="sider">
        <h1 class="brand-title">多模态文档化助手</h1>
        <div class="brand-sub">Multimodal Doc Assistant</div>
        <el-menu class="nav-menu" :default-active="activeMenu">
          <el-menu-item index="video">链接文档化</el-menu-item>
          <el-menu-item index="workflow">任务编排</el-menu-item>
          <el-menu-item index="chat">AI 问答</el-menu-item>
          <el-menu-item index="doc">文档处理</el-menu-item>
          <el-menu-item index="settings">设置</el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="main-area">
        <el-card class="panel-card">
          <div class="toolbar-row">
            <span>视频模板</span>
            <el-select v-model="form.template" style="width: 220px">
              <el-option label="默认通用文字总结 (default_video)" value="default_video" />
            </el-select>
            <el-button type="primary" @click="detectLinkType">识别链接</el-button>
            <el-input v-model="form.url" class="grow" placeholder="粘贴视频/图文链接..." />
            <el-select v-model="form.linkType" style="width: 150px">
              <el-option label="default_video" value="default_video" />
              <el-option label="xiaohongshu" value="xiaohongshu" />
              <el-option label="bilibili" value="bilibili" />
            </el-select>
          </div>

          <div class="config-block">
            <el-checkbox v-model="form.enableFeishu">同步到飞书（生成 MD 后上传至知识库路径）</el-checkbox>
            <el-input v-model="form.titleRule" style="margin-top:8px" placeholder="主任务标题规则（可选，覆盖默认）" />
            <el-input v-model="form.summaryHint" style="margin-top:8px" placeholder="处理策略（AI提示）：输出结构化知识，聚焦业务步骤/风险点。" />
          </div>

          <div class="actions-row">
            <el-button type="primary" :loading="loading" @click="startProcess">开始处理</el-button>
            <el-button @click="batchImport">批量导入</el-button>
            <el-button @click="topTrace">顶层追踪</el-button>
            <el-button @click="rebuildIndex">重建索引</el-button>
            <span class="right">{{ queueText }}</span>
          </div>

          <div class="status-line">{{ statusText }}</div>

          <div class="config-block">
            <div class="prompt-head">
              <b>User Prompt（可选）</b>
              <span class="hint">每次处理按提示词进行微调，最多500字符</span>
              <el-button link class="expand" @click="showPromptEditor = !showPromptEditor">
                {{ showPromptEditor ? "收起编辑" : "展开编辑" }}
              </el-button>
            </div>
            <el-input
              type="textarea"
              :rows="3"
              v-model="form.userPrompt"
              :disabled="!showPromptEditor"
              placeholder="可输入自定义提示词"
            />
          </div>

          <div class="sub-title">外部日志</div>
          <div class="log-box">{{ externalLog }}</div>

          <div class="sub-title">任务链路执行日志</div>
          <div class="log-box">{{ chainLog }}</div>
        </el-card>
      </el-main>
    </el-container>
    `,
  }).use(window.ElementPlus).mount("#app");
})();
