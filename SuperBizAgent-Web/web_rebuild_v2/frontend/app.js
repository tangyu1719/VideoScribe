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

  const { createApp, ref, reactive, onMounted, computed, watch } = window.Vue;

  createApp({
  setup() {
    const activeMenu = ref("video");
    const menuTree = ref([
      { key: "video", title: "链接文档化", children: [] },
      { key: "workflow", title: "任务编排", children: [] },
      { key: "chat", title: "AI问答", children: [] },
      { key: "doc", title: "文档处理", children: [] },
      { key: "settings", title: "设置", children: [] },
      { key: "ops", title: "OPS运维", children: [{ key: "ops_agent", title: "运维AGENT" }, { key: "ops_dashboard", title: "OPS数据可视化" }] },
    ]);
    const opsSubMenu = ref("ops_agent");
    const menuAdminJson = ref("");
    // 防止“卡住”：离开页面时中断长连接/流式读取
    let _activeAbortController = null;
    const abortActive = () => {
      try { _activeAbortController?.abort(); } catch {}
      _activeAbortController = null;
    };
    watch(activeMenu, () => abortActive());

    const appendText = (current, line, maxLen = 20000) => {
      const next = `${current || ""}${current ? "\n" : ""}${line}`;
      return next.length > maxLen ? next.slice(next.length - maxLen) : next;
    };

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
      externalLog.value = appendText(externalLog.value, line, 20000);
    };

    const postJson = async (url, body, { timeoutMs = 15000, signal } = {}) => {
      const controller = new AbortController();
      const t = setTimeout(() => controller.abort(), timeoutMs);
      if (signal) {
        signal.addEventListener("abort", () => {
          try { controller.abort(); } catch {}
        }, { once: true });
      }
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
        signal: controller.signal,
      });
      clearTimeout(t);
      return r.json();
    };

    const callGuiEvent = async (eventId, payload = {}, opts) => {
      return postJson(`${API_BASE}/api/gui/${encodeURIComponent(eventId)}`, { payload }, opts);
    };

    const activeTitle = computed(() => {
      const hit = (menuTree.value || []).find((x) => x.key === activeMenu.value);
      return hit?.title || "链接文档化";
    });

    const loadMenuTree = async () => {
      const r = await fetch(`${API_BASE}/api/menu/tree`);
      const data = await r.json();
      if (!data?.ok) return;
      const tree = data?.data || {};
      const items = tree?.items;
      if (Array.isArray(items) && items.length) {
        menuTree.value = items;
      }
      menuAdminJson.value = JSON.stringify(tree, null, 2);
    };

    const saveMenuTree = async () => {
      let tree = {};
      try {
        tree = JSON.parse(menuAdminJson.value || "{}");
      } catch {
        appendLog("菜单JSON格式错误，无法保存");
        return;
      }
      const data = await postJson(`${API_BASE}/api/menu/tree`, { tree });
      appendLog(data.ok ? "菜单已保存（优先MySQL，失败回退本地）" : `菜单保存失败: ${data.error || "unknown"}`);
      if (data.ok) await loadMenuTree();
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

    // 工作流页
    const wfLog = ref("");
    const wfAppend = (msg) => {
      const line = `[${new Date().toLocaleTimeString()}] ${msg}`;
      wfLog.value = appendText(wfLog.value, line, 20000);
    };
    const wfRun = async () => {
      const data = await postJson(`${API_BASE}/api/workflow/run`, {});
      wfAppend(data.ok ? "执行流程已触发" : `执行失败: ${data.error || "unknown"}`);
      wfLog.value = `${JSON.stringify(data, null, 2)}\n\n${wfLog.value}`;
    };
    const wfResume = async () => {
      const data = await postJson(`${API_BASE}/api/workflow/resume`, {});
      wfAppend(data.ok ? "断点恢复已触发" : `恢复失败: ${data.error || "unknown"}`);
      wfLog.value = `${JSON.stringify(data, null, 2)}\n\n${wfLog.value}`;
    };
    const wfStop = async () => {
      const data = await postJson(`${API_BASE}/api/workflow/stop-current`, {});
      wfAppend(data.ok ? "停止当前已触发" : `停止失败: ${data.error || "unknown"}`);
      wfLog.value = `${JSON.stringify(data, null, 2)}\n\n${wfLog.value}`;
    };
    const wfStartScheduler = async () => {
      const data = await postJson(`${API_BASE}/api/workflow/scheduler/start`, {});
      wfAppend(data.ok ? "调度器启动" : `启动失败: ${data.error || "unknown"}`);
      wfLog.value = `${JSON.stringify(data, null, 2)}\n\n${wfLog.value}`;
    };
    const wfStopScheduler = async () => {
      const data = await postJson(`${API_BASE}/api/workflow/scheduler/stop`, {});
      wfAppend(data.ok ? "调度器停止" : `停止失败: ${data.error || "unknown"}`);
      wfLog.value = `${JSON.stringify(data, null, 2)}\n\n${wfLog.value}`;
    };
    const wfOpenDesigner = async () => {
      const data = await callGuiEvent("open_workflow_designer_window", {});
      wfAppend("打开工作流设计器（事件）");
      wfLog.value = `${JSON.stringify(data, null, 2)}\n\n${wfLog.value}`;
    };
    const wfOpenNodeCenter = async () => {
      const data = await callGuiEvent("open_task_node_center_window", {});
      wfAppend("打开任务节点中心（事件）");
      wfLog.value = `${JSON.stringify(data, null, 2)}\n\n${wfLog.value}`;
    };

    // AI 问答页
    const chatInput = ref("");
    const chatMessages = ref([]);
    const chatThinking = ref("");
    const chatSend = async () => {
      const msg = (chatInput.value || "").trim();
      if (!msg) return;
      abortActive();
      _activeAbortController = new AbortController();
      chatMessages.value.push({ role: "user", content: msg });
      chatInput.value = "";
      chatThinking.value = "";

      try {
        const res = await fetch(`${API_BASE}/api/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: msg, session_id: "default" }),
          signal: _activeAbortController.signal,
        });
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buf = "";
        let currentEvent = "";
        let answerText = "";
        chatMessages.value.push({ role: "assistant", content: "" });
        const idx = chatMessages.value.length - 1;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const parts = buf.split("\n\n");
          buf = parts.pop() || "";
          for (const chunk of parts) {
            const lines = chunk.split("\n");
            let dataLine = "";
            for (const line of lines) {
              if (line.startsWith("event:")) currentEvent = line.slice(6).trim();
              if (line.startsWith("data:")) dataLine += line.slice(5).trim();
            }
            if (!dataLine) continue;
            let data;
            try { data = JSON.parse(dataLine); } catch { continue; }
            if (currentEvent === "thinking_start") chatThinking.value = data.content || "智能助手正在分析...";
            if (currentEvent === "thinking_end") chatThinking.value = "（思考完成）";
            if (currentEvent === "answer_delta") {
              answerText += data.content || "";
              chatMessages.value[idx].content = answerText;
            }
            if (currentEvent === "answer_end") {
              chatMessages.value[idx].content = data.full_text || answerText;
            }
          }
        }
      } catch (e) {
        // 被中断是正常行为（切页/重发）
        if (String(e?.name || "").toLowerCase().includes("abort")) return;
        chatThinking.value = `（异常）${String(e?.message || e)}`;
      } finally {
        _activeAbortController = null;
      }
    };

    // 文档处理页
    const doc = reactive({
      input: {
        source_type: "file",
        path: "",
        meta: {},
      },
      run: {
        status: "idle",
        started_at: null,
        finished_at: null,
        task_id: null,
        error: "",
      },
      output: {
        text_preview: "",
        full_text_ref: "",
        stats: {},
      },
      logs: {
        external: "",
        chain: "",
      },
      ui: {
        alert: null, // {type,title,detail}
        processing: false,
      },
    });

    const docAppendExternal = (msg) => {
      const line = `[${new Date().toLocaleTimeString()}] ${msg}`;
      doc.logs.external = appendText(doc.logs.external, line, 30000);
    };
    const docSetAlert = (type, title, detail = "") => {
      doc.ui.alert = { type, title, detail };
      if (detail) docAppendExternal(`${title}: ${detail}`);
      else docAppendExternal(title);
    };
    const docClearAlert = () => { doc.ui.alert = null; };

    const DOC_ALLOWED_EXT = [".pdf", ".docx", ".md", ".markdown", ".txt", ".png", ".jpg", ".jpeg", ".webp"];
    const docGuessExt = (p) => {
      const s = (p || "").toLowerCase().trim();
      const idx = s.lastIndexOf(".");
      return idx >= 0 ? s.slice(idx) : "";
    };

    const docBrowseFile = async () => {
      docClearAlert();
      const data = await callGuiEvent("browse_workflow_multimodal_file", {});
      doc.logs.chain = JSON.stringify(data, null, 2);
      docAppendExternal("选择文件（事件）已触发");
      // 说明：当前后端 event 还未实现真正的文件选择回填，所以这里保留手动填写路径
      if (!data?.ok) docSetAlert("error", "选择文件失败", data?.error || "unknown");
    };

    const docUploadImage = async () => {
      docClearAlert();
      const data = await callGuiEvent("upload_image", {});
      doc.logs.chain = JSON.stringify(data, null, 2);
      docAppendExternal("上传图片（事件）已触发");
      if (!data?.ok) docSetAlert("error", "上传图片失败", data?.error || "unknown");
    };

    const docOpenRagManager = async () => {
      docClearAlert();
      const data = await callGuiEvent("open_rag_manager", {});
      doc.logs.chain = JSON.stringify(data, null, 2);
      docAppendExternal("打开知识库管理（事件）已触发");
    };

    const docValidateBeforeRun = () => {
      const p = (doc.input.path || "").trim();
      if (!p) {
        docSetAlert("warning", "请先选择文件或输入路径");
        return false;
      }
      const ext = docGuessExt(p);
      if (ext && !DOC_ALLOWED_EXT.includes(ext)) {
        docSetAlert("warning", "文件类型不支持", `仅支持：${DOC_ALLOWED_EXT.join(", ")}`);
        return false;
      }
      return true;
    };

    const docStartProcess = async () => {
      docClearAlert();
      if (!docValidateBeforeRun()) return;

      doc.ui.processing = true;
      doc.run.status = "running";
      doc.run.started_at = Date.now();
      doc.run.finished_at = null;
      doc.run.error = "";
      doc.output.text_preview = "";
      doc.output.full_text_ref = "";
      docAppendExternal("开始处理/转文本：已发起");

      try {
        // 初版：通过 GUI 事件分发占位，payload 先把路径与 source_type 带上
        const payload = {
          source_type: doc.input.source_type,
          path: doc.input.path,
        };
        const data = await callGuiEvent("run_selected_workflow", payload);
        doc.logs.chain = JSON.stringify(data, null, 2);

        if (!data?.ok) {
          doc.run.status = "failed";
          doc.run.error = data?.error || "unknown";
          doc.run.finished_at = Date.now();
          docSetAlert("error", "处理失败", doc.run.error);
          return;
        }

        // 说明：目前后端未返回真实文本产物，这里先做“可验收”的 UI 逻辑闭环
        doc.run.status = "success";
        doc.run.finished_at = Date.now();
        doc.output.text_preview = `（占位预览）已提交处理任务。\nsource_type=${doc.input.source_type}\npath=${doc.input.path}\n\n后续接入真实处理结果后，此处展示前 2000 字符预览。`;
        doc.output.full_text_ref = "(待后端返回产物引用)";
        docSetAlert("success", "已提交处理任务", "等待后端返回真实文本结果");
      } catch (e) {
        doc.run.status = "failed";
        doc.run.error = String(e?.message || e);
        doc.run.finished_at = Date.now();
        docSetAlert("error", "处理异常", doc.run.error);
      } finally {
        doc.ui.processing = false;
      }
    };

    // 设置页（按“二级子菜单”拆分）
    const settingsSubMenu = ref("ai_gateway");
    const settingsModules = reactive({
      ai_gateway: {},
      agent_models: {},
      prompt_center: {},
      runtime_pools: {},
    });
    const opsHistory = ref([]);
    const opsOverview = reactive({
      total_calls: 0,
      success_calls: 0,
      failed_calls: 0,
      avg_cost_ms: 0,
      top_paths: [],
    });
    const opsEvents = ref([]);
    const promptAgentKey = ref("chat_agent");
    const settingsLog = ref("");
    const settingsAppend = (msg) => {
      const line = `[${new Date().toLocaleTimeString()}] ${msg}`;
      settingsLog.value = appendText(settingsLog.value, line, 20000);
    };

    const moduleNameMap = {
      ai_gateway: "AI API 网关与路由",
      agent_models: "Agent & 模型配置",
      prompt_center: "Prompt 配置中心",
      runtime_pools: "系统资源与执行池",
    };

    const settingsLoad = async () => {
      const res = await fetch(`${API_BASE}/api/settings/modules`);
      const data = await res.json();
      if (!data?.ok) {
        settingsAppend(`读取模块设置失败: ${data?.error || "unknown"}`);
        return;
      }
      const got = data.data || {};
      settingsModules.ai_gateway = got.ai_gateway || {};
      settingsModules.agent_models = got.agent_models || {};
      settingsModules.prompt_center = got.prompt_center || {};
      settingsModules.runtime_pools = got.runtime_pools || {};
      settingsModules.ai_gateway.providers = settingsModules.ai_gateway.providers || {};
      settingsModules.ai_gateway.routing = settingsModules.ai_gateway.routing || {};
      settingsModules.ai_gateway.routing.model_pool = settingsModules.ai_gateway.routing.model_pool || [];
      settingsModules.prompt_center.chat_agent = settingsModules.prompt_center.chat_agent || {
        layer1_role_flow: "",
        layer2_rules: "",
        layer2_constraints: "",
        layer2_reply_format: "",
        layer3_eval_strategy: "",
        version: 1,
        updated_at: 0,
        changelog: "",
      };
      settingsModules.prompt_center.doc_standardize_agent = settingsModules.prompt_center.doc_standardize_agent || {
        layer1_role_flow: "", layer2_rules: "", layer2_constraints: "", layer2_reply_format: "", layer3_eval_strategy: "", version: 1, updated_at: 0, changelog: "",
      };
      settingsModules.prompt_center.doc_summarize_agent = settingsModules.prompt_center.doc_summarize_agent || {
        layer1_role_flow: "", layer2_rules: "", layer2_constraints: "", layer2_reply_format: "", layer3_eval_strategy: "", version: 1, updated_at: 0, changelog: "",
      };
      settingsModules.prompt_center.ops_agent = settingsModules.prompt_center.ops_agent || {
        layer1_role_flow: "", layer2_rules: "", layer2_constraints: "", layer2_reply_format: "", layer3_eval_strategy: "", version: 1, updated_at: 0, changelog: "",
      };
      const hist = settingsModules.ai_gateway?.routing?.ops_history || [];
      opsHistory.value = (hist || []).map((it, i) => ({ ...(it || {}), _idx: i })).reverse();
      settingsAppend("读取模块设置完成");
    };

    const loadOpsObservability = async () => {
      const [oRes, eRes] = await Promise.all([
        fetch(`${API_BASE}/api/ops/observability/overview`),
        fetch(`${API_BASE}/api/ops/observability/events?limit=120`),
      ]);
      const oData = await oRes.json();
      const eData = await eRes.json();
      if (oData?.ok) {
        Object.assign(opsOverview, oData.data || {});
      }
      if (eData?.ok) {
        opsEvents.value = (eData.data?.events || []).slice().reverse();
      }
    };

    const settingsSaveCurrentModule = async () => {
      const name = settingsSubMenu.value;
      const data = await postJson(`${API_BASE}/api/settings/modules/${encodeURIComponent(name)}`, {
        data: settingsModules[name] || {},
      });
      settingsAppend(data.ok ? `保存完成：${moduleNameMap[name] || name}` : `保存失败: ${data.error || "unknown"}`);
      settingsLog.value = `${JSON.stringify(data, null, 2)}\n\n${settingsLog.value}`;
    };

    const addRouteModel = () => {
      const routing = settingsModules.ai_gateway.routing || (settingsModules.ai_gateway.routing = {});
      const pool = routing.model_pool || (routing.model_pool = []);
      pool.push({ model_id: "", weight: 50, status: "active" });
    };
    const removeRouteModel = (idx) => {
      const pool = settingsModules.ai_gateway?.routing?.model_pool || [];
      pool.splice(idx, 1);
    };

    const opsMarkFailed = async () => {
      const data = await postJson(`${API_BASE}/api/ops/route/mark-failed`, {
        model_id: "ep-demo",
        error_type: "timeout",
        context: { source: "settings-ui" },
      });
      settingsAppend(data.ok ? "运维记录失败事件成功" : `运维记录失败: ${data.error || "unknown"}`);
      settingsLog.value = `${JSON.stringify(data, null, 2)}\n\n${settingsLog.value}`;
    };

    const opsReconfigure = async () => {
      const data = await postJson(`${API_BASE}/api/ops/route/reconfigure`, {
        model_id: "ep-demo",
        action: "degrade_weight",
      });
      settingsAppend(data.ok ? "运维路由调配成功" : `运维调配失败: ${data.error || "unknown"}`);
      settingsLog.value = `${JSON.stringify(data, null, 2)}\n\n${settingsLog.value}`;
    };

    const opsSuggestions = async () => {
      const res = await fetch(`${API_BASE}/api/ops/route/suggestions`);
      const data = await res.json();
      settingsAppend(data.ok ? "获取运维建议成功" : `获取建议失败: ${data.error || "unknown"}`);
      settingsLog.value = `${JSON.stringify(data, null, 2)}\n\n${settingsLog.value}`;
    };
    const opsRollbackLast = async () => {
      const data = await postJson(`${API_BASE}/api/ops/route/rollback-last`, { history_index: -1 });
      settingsAppend(data.ok ? "已回滚上一步运维调配" : `回滚失败: ${data.error || "unknown"}`);
      settingsLog.value = `${JSON.stringify(data, null, 2)}\n\n${settingsLog.value}`;
      await settingsLoad();
    };
    const opsRollbackByIndex = async (idx) => {
      const data = await postJson(`${API_BASE}/api/ops/route/rollback-last`, { history_index: idx });
      settingsAppend(data.ok ? `已回滚指定历史 #${idx}` : `回滚失败: ${data.error || "unknown"}`);
      settingsLog.value = `${JSON.stringify(data, null, 2)}\n\n${settingsLog.value}`;
      await settingsLoad();
    };
    const promptCopyToOthers = () => {
      const srcKey = promptAgentKey.value;
      const src = settingsModules.prompt_center[srcKey] || {};
      const keys = ["chat_agent", "doc_standardize_agent", "doc_summarize_agent", "ops_agent"];
      keys.forEach((k) => {
        if (k === srcKey) return;
        settingsModules.prompt_center[k] = {
          ...(settingsModules.prompt_center[k] || {}),
          layer1_role_flow: src.layer1_role_flow || "",
          layer2_rules: src.layer2_rules || "",
          layer2_constraints: src.layer2_constraints || "",
          layer2_reply_format: src.layer2_reply_format || "",
          layer3_eval_strategy: src.layer3_eval_strategy || "",
          changelog: (settingsModules.prompt_center[k]?.changelog || "") + "\n[copy] 从 " + srcKey + " 复制模板",
        };
      });
      settingsAppend(`已将 ${srcKey} 模板复制到其他 Agent`);
    };
    const openAiApiConfig = async () => {
      const data = await callGuiEvent("open_ai_api_config_window", {});
      settingsAppend("打开 AI API 配置（事件）");
      settingsLog.value = `${JSON.stringify(data, null, 2)}\n\n${settingsLog.value}`;
    };
    const openThreadConfig = async () => {
      const data = await callGuiEvent("open_thread_config_window", {});
      settingsAppend("打开线程配置（事件）");
      settingsLog.value = `${JSON.stringify(data, null, 2)}\n\n${settingsLog.value}`;
    };

    onMounted(async () => {
      await loadMenuTree();
      await callGuiEvent("show_video_page");
      await settingsLoad();
      await loadOpsObservability();
      appendLog("页面已就绪（Vue + Element Plus）");
    });

    return {
      activeMenu,
      menuTree,
      opsSubMenu,
      menuAdminJson,
      activeTitle,
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
      wfLog,
      wfRun,
      wfResume,
      wfStop,
      wfStartScheduler,
      wfStopScheduler,
      wfOpenDesigner,
      wfOpenNodeCenter,
      chatInput,
      chatMessages,
      chatThinking,
      chatSend,
      docUploadImage,
      docBrowseFile,
      docOpenRagManager,
      doc,
      docStartProcess,
      docClearAlert,
      settingsSubMenu,
      settingsModules,
      settingsLog,
      settingsLoad,
      settingsSaveCurrentModule,
      addRouteModel,
      removeRouteModel,
      openAiApiConfig,
      openThreadConfig,
      opsMarkFailed,
      opsReconfigure,
      opsSuggestions,
      opsRollbackLast,
      opsRollbackByIndex,
      opsHistory,
      opsOverview,
      opsEvents,
      loadOpsObservability,
      loadMenuTree,
      saveMenuTree,
      promptAgentKey,
      promptCopyToOthers,
    };
  },
    template: `
    <el-container class="page-root">
      <el-aside width="220px" class="sider">
        <h1 class="brand-title">多模态文档化助手</h1>
        <div class="brand-sub">Multimodal Doc Assistant</div>
        <el-menu class="nav-menu" :default-active="activeMenu" @select="(k)=> activeMenu=k">
          <el-menu-item v-for="m in menuTree" :key="m.key" :index="m.key">{{ m.title }}</el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="main-area">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
          <h2 style="margin:0;font-size:18px;color:#111827">{{ activeTitle }}</h2>
        </div>

        <el-card class="panel-card" v-if="activeMenu==='video'">
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

        <el-card class="panel-card" v-else-if="activeMenu==='workflow'">
          <div class="actions-row">
            <el-button type="primary" @click="wfRun">执行流程</el-button>
            <el-button @click="wfResume">断点恢复</el-button>
            <el-button @click="wfStop">停止当前</el-button>
            <el-button @click="wfStartScheduler">启动调度器</el-button>
            <el-button @click="wfStopScheduler">停止调度器</el-button>
            <el-button @click="wfOpenDesigner">工作流设计器</el-button>
            <el-button @click="wfOpenNodeCenter">任务节点中心</el-button>
          </div>
          <div class="sub-title">执行日志</div>
          <div class="log-box">{{ wfLog }}</div>
        </el-card>

        <el-card class="panel-card" v-else-if="activeMenu==='chat'">
          <div class="config-block">
            <div class="sub-title" style="margin-top:0">思考过程</div>
            <div class="log-box" style="min-height:80px;max-height:120px">{{ chatThinking }}</div>
          </div>
          <div class="config-block">
            <div class="sub-title" style="margin-top:0">对话</div>
            <div class="log-box" style="min-height:220px;max-height:320px">
              <div v-for="(m,i) in chatMessages" :key="i" style="margin-bottom:8px">
                <b>{{ m.role==='user'?'User':'Assistant' }}:</b> {{ m.content }}
              </div>
            </div>
            <div class="toolbar-row" style="margin-top:10px">
              <el-input v-model="chatInput" class="grow" placeholder="输入问题..." />
              <el-button type="primary" @click="chatSend">发送</el-button>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card" v-else-if="activeMenu==='doc'">
          <el-alert
            v-if="doc.ui.alert"
            :type="doc.ui.alert.type"
            :title="doc.ui.alert.title"
            :closable="true"
            show-icon
            style="margin-bottom:10px"
            @close="docClearAlert"
          >
            <template #default>
              <div v-if="doc.ui.alert.detail" style="white-space:pre-wrap">{{ doc.ui.alert.detail }}</div>
            </template>
          </el-alert>

          <div class="config-block">
            <div class="sub-title" style="margin-top:0">输入</div>
            <div class="actions-row">
              <el-select v-model="doc.input.source_type" style="width:160px">
                <el-option label="文件" value="file" />
                <el-option label="图片" value="image" />
                <el-option label="文件夹" value="folder" />
                <el-option label="URL" value="url" />
              </el-select>
              <el-input v-model="doc.input.path" class="grow" placeholder="输入或回填本地路径，例如：C:\docs\a.pdf" />
              <el-button type="primary" @click="docBrowseFile">选择文件</el-button>
              <el-button @click="docUploadImage">选择/上传图片</el-button>
              <el-button @click="docOpenRagManager">知识库管理</el-button>
            </div>
          </div>

          <div class="config-block">
            <div class="sub-title" style="margin-top:0">执行</div>
            <div class="actions-row">
              <el-button type="primary" :loading="doc.ui.processing" @click="docStartProcess">开始处理 / 转文本</el-button>
              <span class="right">状态：{{ doc.run.status }}</span>
            </div>
          </div>

          <div class="config-block">
            <div class="sub-title" style="margin-top:0">输出预览</div>
            <el-input type="textarea" :rows="6" v-model="doc.output.text_preview" placeholder="处理完成后展示前 2000 字符预览" />
            <div style="margin-top:8px;color:#6b7280;font-size:12px">产物引用：{{ doc.output.full_text_ref || "-" }}</div>
          </div>

          <div class="sub-title">外部日志</div>
          <div class="log-box">{{ doc.logs.external }}</div>

          <div class="sub-title">链路日志</div>
          <div class="log-box">{{ doc.logs.chain }}</div>
        </el-card>

        <el-card class="panel-card" v-else-if="activeMenu==='settings'">
          <div class="actions-row">
            <el-button @click="settingsLoad">读取设置</el-button>
            <el-button type="primary" @click="settingsSaveCurrentModule">保存当前子模块</el-button>
            <el-button @click="openAiApiConfig">AI API 配置</el-button>
            <el-button @click="openThreadConfig">系统资源配置</el-button>
            <el-button @click="opsMarkFailed">运维记录失败</el-button>
            <el-button @click="opsReconfigure">运维路由调配</el-button>
            <el-button @click="opsSuggestions">运维建议</el-button>
            <el-button @click="opsRollbackLast">回滚上一步</el-button>
          </div>
          <div class="settings-layout">
            <div class="settings-subnav">
              <el-menu :default-active="settingsSubMenu" @select="(k)=>settingsSubMenu=k">
                <el-menu-item index="ai_gateway">AI API 网关与路由</el-menu-item>
                <el-menu-item index="agent_models">Agent & 模型配置</el-menu-item>
                <el-menu-item index="prompt_center">Prompt 配置中心</el-menu-item>
                <el-menu-item index="runtime_pools">系统资源与执行池</el-menu-item>
                <el-menu-item index="menu_admin">菜单管理</el-menu-item>
              </el-menu>
            </div>
            <div class="settings-detail">
              <div class="sub-title" style="margin-top:0">当前子模块：{{ settingsSubMenu }}</div>
              <template v-if="settingsSubMenu==='ai_gateway'">
                <div class="config-block">
                  <div class="toolbar-row">
                    <span>Provider</span>
                    <el-select v-model="settingsModules.ai_gateway.provider" style="width:180px">
                      <el-option label="Ark" value="ark" />
                      <el-option label="OpenAI" value="openai" />
                      <el-option label="Anthropic" value="anthropic" />
                    </el-select>
                    <span>路由模式</span>
                    <el-select v-model="settingsModules.ai_gateway.routing.mode" style="width:180px">
                      <el-option label="priority" value="priority" />
                      <el-option label="weight" value="weight" />
                      <el-option label="task_type" value="task_type" />
                    </el-select>
                  </div>
                  <el-input v-model="settingsModules.ai_gateway.providers[settingsModules.ai_gateway.provider].base_url" placeholder="Base URL" style="margin-bottom:8px" />
                  <el-input v-model="settingsModules.ai_gateway.providers[settingsModules.ai_gateway.provider].api_key" placeholder="API Key" style="margin-bottom:8px" />
                  <el-input
                    v-if="settingsModules.ai_gateway.provider==='ark'"
                    v-model="settingsModules.ai_gateway.providers.ark.endpoint_id"
                    placeholder="Ark endpoint_id"
                    style="margin-bottom:8px"
                  />
                  <el-input
                    v-if="settingsModules.ai_gateway.provider!=='ark'"
                    v-model="settingsModules.ai_gateway.providers[settingsModules.ai_gateway.provider].model"
                    placeholder="Model"
                    style="margin-bottom:8px"
                  />
                  <el-input-number
                    v-model="settingsModules.ai_gateway.providers[settingsModules.ai_gateway.provider].timeout_sec"
                    :min="10"
                    :max="600"
                    style="width:220px"
                  />
                </div>
                <div class="config-block">
                  <div class="toolbar-row">
                    <b>模型池（运维可调配）</b>
                    <el-button size="small" @click="addRouteModel">新增模型</el-button>
                  </div>
                  <div v-for="(m,idx) in (settingsModules.ai_gateway.routing.model_pool || [])" :key="idx" class="toolbar-row">
                    <el-input v-model="m.model_id" placeholder="model_id" class="grow" />
                    <el-input-number v-model="m.weight" :min="0" :max="1000" />
                    <el-select v-model="m.status" style="width:120px">
                      <el-option label="active" value="active" />
                      <el-option label="disabled" value="disabled" />
                    </el-select>
                    <el-button type="danger" link @click="removeRouteModel(idx)">删除</el-button>
                  </div>
                </div>
                <div class="config-block">
                  <div class="sub-title" style="margin-top:0">运维路由操作历史</div>
                  <el-table :data="opsHistory" size="small" style="width:100%">
                    <el-table-column prop="updated_at" label="时间" width="170" />
                    <el-table-column prop="action" label="动作" width="130" />
                    <el-table-column prop="model_id" label="模型" />
                    <el-table-column label="前后状态差异">
                      <template #default="scope">
                        <span style="font-size:12px;color:#6b7280">
                          {{ (scope.row.before && scope.row.after) ? (JSON.stringify(scope.row.before) + ' => ' + JSON.stringify(scope.row.after)) : '-' }}
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="120">
                      <template #default="scope">
                        <el-button size="small" @click="opsRollbackByIndex(scope.row._idx)">回滚到此</el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </template>

              <template v-else-if="settingsSubMenu==='agent_models'">
                <div class="config-block" v-for="(cfg,name) in settingsModules.agent_models" :key="name">
                  <div class="sub-title" style="margin-top:0">{{ name }}</div>
                  <div class="toolbar-row">
                    <span>策略</span>
                    <el-select v-model="cfg.strategy" style="width:180px">
                      <el-option label="按路由 route" value="route" />
                      <el-option label="优先级 priority" value="priority" />
                      <el-option label="强制指定 forced" value="forced" />
                    </el-select>
                    <span>强制模型</span>
                    <el-input v-model="cfg.forced_model" placeholder="forced model id" class="grow" />
                  </div>
                  <div class="toolbar-row">
                    <span>temperature</span>
                    <el-input-number v-model="cfg.temperature" :min="0" :max="2" :step="0.1" />
                    <span>top_p</span>
                    <el-input-number v-model="cfg.top_p" :min="0" :max="1" :step="0.05" />
                  </div>
                </div>
              </template>

              <template v-else-if="settingsSubMenu==='prompt_center'">
                <div class="config-block">
                  <div class="toolbar-row">
                    <span>Agent</span>
                    <el-select v-model="promptAgentKey" style="width:240px">
                      <el-option label="chat_agent（对话调度）" value="chat_agent" />
                      <el-option label="doc_standardize_agent（原始文档标准化）" value="doc_standardize_agent" />
                      <el-option label="doc_summarize_agent（文档摘要化）" value="doc_summarize_agent" />
                      <el-option label="ops_agent（系统运维）" value="ops_agent" />
                    </el-select>
                    <el-button @click="promptCopyToOthers">一键复制当前模板到其他Agent</el-button>
                  </div>
                </div>
                <div class="config-block">
                  <div class="toolbar-row">
                    <span>版本</span>
                    <el-input-number v-model="settingsModules.prompt_center[promptAgentKey].version" :min="1" :max="9999" />
                    <span>更新时间</span>
                    <el-input v-model="settingsModules.prompt_center[promptAgentKey].updated_at" class="grow" disabled />
                  </div>
                  <div class="sub-title" style="margin-top:0">变更说明</div>
                  <el-input type="textarea" :rows="2" v-model="settingsModules.prompt_center[promptAgentKey].changelog" />
                </div>
                <div class="config-block">
                  <div class="sub-title" style="margin-top:0">{{ promptAgentKey }} · 第一层（业务定位与流程）</div>
                  <el-input type="textarea" :rows="5" v-model="settingsModules.prompt_center[promptAgentKey].layer1_role_flow" />
                </div>
                <div class="config-block">
                  <div class="sub-title" style="margin-top:0">第二层A（规范）</div>
                  <el-input type="textarea" :rows="4" v-model="settingsModules.prompt_center[promptAgentKey].layer2_rules" />
                  <div class="sub-title">第二层B（约束）</div>
                  <el-input type="textarea" :rows="4" v-model="settingsModules.prompt_center[promptAgentKey].layer2_constraints" />
                  <div class="sub-title">第二层C（回复格式）</div>
                  <el-input type="textarea" :rows="4" v-model="settingsModules.prompt_center[promptAgentKey].layer2_reply_format" />
                </div>
                <div class="config-block">
                  <div class="sub-title" style="margin-top:0">第三层（评测润色与扩展，不直接注入）</div>
                  <el-input type="textarea" :rows="4" v-model="settingsModules.prompt_center[promptAgentKey].layer3_eval_strategy" />
                </div>
              </template>

              <template v-else-if="settingsSubMenu==='menu_admin'">
                <div class="actions-row">
                  <el-button @click="loadMenuTree">加载菜单</el-button>
                  <el-button type="primary" @click="saveMenuTree">保存菜单</el-button>
                  <span style="color:#6b7280;font-size:12px">优先写入 MySQL（环境变量配置），失败则回退本地文件。</span>
                </div>
                <el-input type="textarea" :rows="16" v-model="menuAdminJson" placeholder="菜单树 JSON" />
              </template>

              <template v-else>
                <div class="config-block">
                  <div class="toolbar-row">
                    <span>系统工作线程</span>
                    <el-input-number v-model="settingsModules.runtime_pools.system_workers" :min="1" :max="128" />
                    <span>RAG线程</span>
                    <el-input-number v-model="settingsModules.runtime_pools.rag_workers" :min="1" :max="128" />
                  </div>
                  <div class="toolbar-row">
                    <span>Whisper池</span>
                    <el-input-number v-model="settingsModules.runtime_pools.whisper_pool_size" :min="1" :max="32" />
                    <span>MinerU线程</span>
                    <el-input-number v-model="settingsModules.runtime_pools.mineru_workers" :min="1" :max="32" />
                    <span>队列上限</span>
                    <el-input-number v-model="settingsModules.runtime_pools.queue_max_size" :min="1" :max="10000" />
                  </div>
                </div>
              </template>
            </div>
          </div>
          <div class="sub-title">操作日志</div>
          <div class="log-box">{{ settingsLog }}</div>
        </el-card>

        <el-card class="panel-card" v-else-if="activeMenu==='ops'">
          <div class="settings-layout">
            <div class="settings-subnav">
              <el-menu :default-active="opsSubMenu" @select="(k)=>opsSubMenu=k">
                <el-menu-item index="ops_agent">运维AGENT</el-menu-item>
                <el-menu-item index="ops_dashboard">OPS数据可视化</el-menu-item>
              </el-menu>
            </div>
            <div class="settings-detail">
              <template v-if="opsSubMenu==='ops_agent'">
                <div class="config-block">
                  <div class="sub-title" style="margin-top:0">运维AGENT执行框架</div>
                  <el-tag type="success">ReAct</el-tag>
                  <div style="margin-top:8px;color:#475569;font-size:12px">Thought -> Action -> Observation，失败后重规划与补偿。</div>
                </div>
                <div class="config-block">
                  <div class="sub-title" style="margin-top:0">运维AGENT Prompt（第二层规范/约束）</div>
                  <el-input type="textarea" :rows="4" v-model="settingsModules.prompt_center.ops_agent.layer2_rules" placeholder="规范（怎么做）" />
                  <el-input type="textarea" :rows="4" v-model="settingsModules.prompt_center.ops_agent.layer2_constraints" placeholder="约束（不能怎么做）" style="margin-top:8px" />
                  <el-input type="textarea" :rows="4" v-model="settingsModules.prompt_center.ops_agent.layer2_reply_format" placeholder="回复格式规范" style="margin-top:8px" />
                  <div class="actions-row" style="margin-top:8px">
                    <el-button type="primary" @click="settingsSubMenu='prompt_center'; promptAgentKey='ops_agent'; settingsSaveCurrentModule()">保存运维AGENT配置</el-button>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="actions-row">
                  <el-button type="primary" @click="loadOpsObservability">刷新运维数据</el-button>
                </div>
                <div class="ops-overview-grid">
                  <div class="ops-metric-card"><div class="k">总调用</div><div class="v">{{ opsOverview.total_calls }}</div></div>
                  <div class="ops-metric-card"><div class="k">成功</div><div class="v">{{ opsOverview.success_calls }}</div></div>
                  <div class="ops-metric-card"><div class="k">失败</div><div class="v">{{ opsOverview.failed_calls }}</div></div>
                  <div class="ops-metric-card"><div class="k">平均耗时(ms)</div><div class="v">{{ opsOverview.avg_cost_ms }}</div></div>
                </div>
                <div class="config-block">
                  <div class="sub-title" style="margin-top:0">高频接口</div>
                  <el-table :data="opsOverview.top_paths || []" size="small" style="width:100%">
                    <el-table-column prop="path" label="接口路径" />
                    <el-table-column prop="count" label="调用次数" width="120" />
                  </el-table>
                </div>
                <div class="config-block">
                  <div class="sub-title" style="margin-top:0">统一日志平面事件流</div>
                  <el-table :data="opsEvents" size="small" style="width:100%">
                    <el-table-column prop="ts" label="时间" width="140" />
                    <el-table-column prop="method" label="方法" width="90" />
                    <el-table-column prop="path" label="路径" />
                    <el-table-column prop="status_code" label="状态" width="90" />
                    <el-table-column prop="cost_ms" label="耗时ms" width="90" />
                  </el-table>
                </div>
              </template>
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>
    `,
  }).use(window.ElementPlus).mount("#app");
})();
