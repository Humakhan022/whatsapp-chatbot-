/**
 * WhatsApp AI Chatbot & Dataset Management Studio
 * Interactive Frontend Engine
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentDataset = null;
  let activeTab = "simulator";
  const sessionId = "wa_session_" + Math.random().toString(36).substring(2, 9);

  // DOM Elements
  const datasetDropdown = document.getElementById("datasetDropdown");
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const openDatasetDrawerBtn = document.getElementById("openDatasetDrawerBtn");
  const closeDatasetDrawerBtn = document.getElementById("closeDatasetDrawerBtn");
  const datasetDrawerOverlay = document.getElementById("datasetDrawerOverlay");

  const openApiGuideBtn = document.getElementById("openApiGuideBtn");
  const closeApiGuideBtn = document.getElementById("closeApiGuideBtn");
  const closeApiGuideFooterBtn = document.getElementById("closeApiGuideFooterBtn");
  const apiGuideModal = document.getElementById("apiGuideModal");

  // Profile Elements
  const sidebarBotName = document.getElementById("sidebarBotName");
  const sidebarBotTagline = document.getElementById("sidebarBotTagline");
  const sidebarCategoryBadge = document.getElementById("sidebarCategoryBadge");
  const waContactName = document.getElementById("waContactName");

  // Chat Elements
  const waChatBody = document.getElementById("waChatBody");
  const messagesContainer = document.getElementById("messagesContainer");
  const initialBotMessage = document.getElementById("initialBotMessage");
  const initialSenderName = document.getElementById("initialSenderName");
  const initialMessageContent = document.getElementById("initialMessageContent");
  const initialMessageTime = document.getElementById("initialMessageTime");
  const typingIndicator = document.getElementById("typingIndicator");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const quickRepliesContainer = document.getElementById("quickRepliesContainer");
  const clearChatBtn = document.getElementById("clearChatBtn");

  // Presets & Analytics
  const presetCardsList = document.getElementById("presetCardsList");
  const quickPromptChips = document.getElementById("quickPromptChips");

  // Drawer Elements
  const drawerBotName = document.getElementById("drawerBotName");
  const drawerIntentsCount = document.getElementById("drawerIntentsCount");
  const kbTableBody = document.getElementById("kbTableBody");
  const kbSearchInput = document.getElementById("kbSearchInput");
  const toggleAddEntryBtn = document.getElementById("toggleAddEntryBtn");
  const addEntryForm = document.getElementById("addEntryForm");
  const addEntryChevron = document.getElementById("addEntryChevron");
  const datasetFileInput = document.getElementById("datasetFileInput");
  const exportDatasetBtn = document.getElementById("exportDatasetBtn");

  // ---------------- FORMATTING HELPERS ----------------

  function formatWhatsAppMarkdown(text) {
    if (!text) return "";
    let formatted = text
      // Escape HTML entities
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      // Bold: *text*
      .replace(/\*(.*?)\*/g, "<strong>$1</strong>")
      // Italic: _text_
      .replace(/_(.*?)_/g, "<em>$1</em>")
      // Code: `text`
      .replace(/`(.*?)`/g, "<code>$1</code>")
      // Strikethrough: ~text~
      .replace(/~(.*?)~/g, "<del>$1</del>");

    // URLs to clickable links
    formatted = formatted.replace(
      /(https?:\/\/[^\s]+)/g,
      '<a href="$1" target="_blank" rel="noopener" style="color:var(--wa-green); text-decoration:underline;">$1</a>'
    );

    return formatted;
  }

  function getLocalTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    hours = hours ? hours : 12;
    minutes = minutes < 10 ? "0" + minutes : minutes;
    return `${hours}:${minutes} ${ampm}`;
  }

  function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "fa-circle-check" : "fa-triangle-exclamation";
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // ---------------- THEME TOGGLING ----------------

  const savedTheme = localStorage.getItem("wa_bot_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);

  themeToggleBtn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("wa_bot_theme", next);
    updateThemeIcon(next);
  });

  function updateThemeIcon(theme) {
    themeToggleBtn.innerHTML = theme === "dark" 
      ? '<i class="fa-solid fa-sun"></i>' 
      : '<i class="fa-solid fa-moon"></i>';
  }

  // ---------------- INITIAL DATASET LOADING ----------------

  async function loadInitialData() {
    try {
      const res = await fetch("/api/dataset/current");
      const data = await res.json();
      if (data.status === "success") {
        currentDataset = data.dataset;
        updateUIWithDataset(currentDataset);
      }
      await loadPresetsList();
    } catch (err) {
      console.error("Failed to load initial dataset", err);
    }
  }

  function updateUIWithDataset(ds) {
    sidebarBotName.textContent = ds.bot_name;
    sidebarBotTagline.textContent = ds.bot_tagline;
    sidebarCategoryBadge.textContent = ds.category;
    waContactName.textContent = ds.bot_name;
    drawerBotName.textContent = ds.bot_name;
    drawerIntentsCount.textContent = ds.total_intents;

    // Welcome message
    initialSenderName.textContent = ds.bot_name;
    initialMessageContent.innerHTML = formatWhatsAppMarkdown(ds.welcome_message);
    initialMessageTime.textContent = getLocalTime();

    // Render Quick Replies
    renderQuickReplies(ds.quick_replies);

    // Sync Dropdown
    if (datasetDropdown.querySelector(`option[value="${ds.active_dataset_id}"]`)) {
      datasetDropdown.value = ds.active_dataset_id;
    }

    // Render Table in Drawer
    renderKnowledgeBaseTable(ds.knowledge_base);
  }

  async function loadPresetsList() {
    try {
      const res = await fetch("/api/datasets");
      const data = await res.json();
      presetCardsList.innerHTML = "";

      // Ensure dropdown options match presets
      datasetDropdown.innerHTML = "";
      data.presets.forEach(preset => {
        const opt = document.createElement("option");
        opt.value = preset.id;
        opt.textContent = `${preset.name} (${preset.type})`;
        datasetDropdown.appendChild(opt);

        // Sidebar Preset Card
        const card = document.createElement("div");
        card.className = `preset-card ${preset.id === data.active_dataset_id ? "active" : ""}`;
        card.innerHTML = `
          <div class="preset-card-title">
            <span>${preset.name}</span>
            <span class="preset-badge">${preset.type}</span>
          </div>
          <div class="preset-card-desc">Click to switch bot dataset to ${preset.name}</div>
        `;
        card.addEventListener("click", () => switchActiveDataset(preset.id));
        presetCardsList.appendChild(card);
      });

      datasetDropdown.value = data.active_dataset_id;
    } catch (err) {
      console.error("Error loading presets:", err);
    }
  }

  async function switchActiveDataset(datasetId) {
    try {
      const res = await fetch("/api/dataset/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId })
      });
      const data = await res.json();
      if (data.status === "success") {
        currentDataset = data.summary;
        updateUIWithDataset(currentDataset);
        await loadPresetsList();
        showToast(`Activated dataset: ${currentDataset.bot_name}`);
      } else {
        showToast(data.message || "Failed to switch dataset", "error");
      }
    } catch (err) {
      showToast("Error switching dataset", "error");
    }
  }

  datasetDropdown.addEventListener("change", (e) => {
    switchActiveDataset(e.target.value);
  });

  // ---------------- CHAT HANDLING ----------------

  function renderQuickReplies(replies) {
    quickRepliesContainer.innerHTML = "";
    if (!replies || replies.length === 0) return;

    replies.forEach(replyText => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quick-reply-pill";
      btn.innerHTML = `<i class="fa-solid fa-bolt-lightning"></i> ${replyText}`;
      btn.addEventListener("click", () => {
        sendMessage(replyText);
      });
      quickRepliesContainer.appendChild(btn);
    });
  }

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed) return;

    // Append outgoing bubble
    appendOutgoingBubble(trimmed);
    messageInput.value = "";
    scrollToBottom();

    // Show typing indicator
    typingIndicator.classList.remove("hidden");
    scrollToBottom();

    try {
      const startTime = Date.now();
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          session_id: sessionId
        })
      });
      const data = await res.json();

      // Ensure at least a natural 350ms delay for WhatsApp typing animation feel
      const elapsed = Date.now() - startTime;
      const delay = Math.max(350 - elapsed, 100);

      setTimeout(() => {
        typingIndicator.classList.add("hidden");
        appendIncomingBubble(data);
        if (data.quick_replies) {
          renderQuickReplies(data.quick_replies);
        }
        scrollToBottom();
      }, delay);

    } catch (err) {
      typingIndicator.classList.add("hidden");
      appendIncomingBubble({
        reply: "Sorry, I ran into an issue connecting to the engine. Please try again.",
        confidence: 0,
        matched_intent: "network_error"
      });
      scrollToBottom();
    }
  }

  function appendOutgoingBubble(text) {
    const row = document.createElement("div");
    row.className = "message-row outgoing";
    row.innerHTML = `
      <div class="message-bubble">
        <div class="message-content">${formatWhatsAppMarkdown(text)}</div>
        <div class="message-meta">
          <span class="message-time">${getLocalTime()}</span>
          <i class="fa-solid fa-check-double ticks-blue" title="Read"></i>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
  }

  function appendIncomingBubble(data) {
    const row = document.createElement("div");
    row.className = "message-row incoming";

    const isHighConfidence = (data.confidence || 0) >= 0.7;
    const badgeClass = isHighConfidence ? "match-badge" : "match-badge low-confidence";
    const confidencePct = Math.round((data.confidence || 0) * 100);

    const intentTag = data.matched_intent ? `
      <div class="${badgeClass}" title="Engine Matching Score">
        <i class="fa-solid fa-bullseye"></i> ${data.matched_intent} (${confidencePct}%)
      </div>
    ` : "";

    row.innerHTML = `
      <div class="message-bubble">
        <div class="message-sender-name">${currentDataset ? currentDataset.bot_name : "Assistant"}</div>
        <div class="message-content">${formatWhatsAppMarkdown(data.reply)}</div>
        ${intentTag}
        <div class="message-meta">
          <span class="message-time">${data.timestamp || getLocalTime()}</span>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
  }

  function scrollToBottom() {
    waChatBody.scrollTop = waChatBody.scrollHeight;
  }

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(messageInput.value);
  });

  // Prompt chips in sidebar
  quickPromptChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".prompt-chip");
    if (chip && chip.dataset.query) {
      sendMessage(chip.dataset.query);
    }
  });

  clearChatBtn.addEventListener("click", () => {
    messagesContainer.innerHTML = "";
    showToast("Chat cleared");
  });

  // ---------------- SIDEBAR TABS ----------------

  document.querySelectorAll(".sidebar-tabs .nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".sidebar-tabs .nav-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      tab.classList.add("active");

      const target = tab.dataset.tab;
      activeTab = target;
      if (target === "simulator") {
        document.getElementById("tabContentSimulator").classList.add("active");
      } else if (target === "presets") {
        document.getElementById("tabContentPresets").classList.add("active");
      } else if (target === "analytics") {
        document.getElementById("tabContentAnalytics").classList.add("active");
        loadAnalytics();
      }
    });
  });

  async function loadAnalytics() {
    try {
      const res = await fetch("/api/analytics");
      const data = await res.json();
      if (data.status === "success") {
        const a = data.analytics;
        document.getElementById("statTotalQueries").textContent = a.total_messages;
        const total = a.total_messages || 1;
        const matchPct = Math.round(((a.matched_queries || 0) / total) * 100);
        document.getElementById("statMatchRate").textContent = `${matchPct}%`;
        document.getElementById("statTotalIntents").textContent = data.total_intents;
        document.getElementById("statFallbackCount").textContent = a.fallback_queries;

        // Render top intents list
        const intentsList = document.getElementById("intentsDistributionList");
        const triggers = a.intents_triggered || {};
        const entries = Object.entries(triggers).sort((x, y) => y[1] - x[1]);

        if (entries.length === 0) {
          intentsList.innerHTML = `<p class="empty-hint">Interact with the bot to see real-time trigger frequencies!</p>`;
        } else {
          intentsList.innerHTML = entries.map(([intent, count]) => `
            <div class="intent-row">
              <span class="intent-name">${intent}</span>
              <span class="intent-hits">${count} hits</span>
            </div>
          `).join("");
        }
      }
    } catch (err) {
      console.error("Error loading analytics:", err);
    }
  }

  // ---------------- DATASET MANAGER DRAWER ----------------

  function openDatasetDrawer() {
    datasetDrawerOverlay.classList.remove("hidden");
    if (currentDataset) {
      renderKnowledgeBaseTable(currentDataset.knowledge_base);
    }
  }

  function closeDatasetDrawer() {
    datasetDrawerOverlay.classList.add("hidden");
  }

  openDatasetDrawerBtn.addEventListener("click", openDatasetDrawer);
  closeDatasetDrawerBtn.addEventListener("click", closeDatasetDrawer);
  document.getElementById("openSettingsQuick").addEventListener("click", openDatasetDrawer);
  document.getElementById("uploadSidebarBtn").addEventListener("click", () => {
    datasetFileInput.click();
  });

  datasetDrawerOverlay.addEventListener("click", (e) => {
    if (e.target === datasetDrawerOverlay) {
      closeDatasetDrawer();
    }
  });

  // Toggle Add Entry Form
  toggleAddEntryBtn.addEventListener("click", () => {
    addEntryForm.classList.toggle("hidden");
    addEntryChevron.classList.toggle("fa-chevron-up");
  });

  // Save new entry
  addEntryForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const intent = document.getElementById("intentNameInput").value.trim();
    const patterns = document.getElementById("patternsInput").value.trim();
    const response = document.getElementById("responseInput").value.trim();
    const quickReplies = document.getElementById("quickRepliesInput").value.trim();

    try {
      const res = await fetch("/api/dataset/entry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          intent: intent,
          patterns: patterns,
          response: response,
          quick_replies: quickReplies
        })
      });
      const data = await res.json();
      if (data.status === "success") {
        showToast("New knowledge entry saved to bot!");
        addEntryForm.reset();
        addEntryForm.classList.add("hidden");
        // Reload current dataset
        const curRes = await fetch("/api/dataset/current");
        const curData = await curRes.json();
        currentDataset = curData.dataset;
        updateUIWithDataset(currentDataset);
      } else {
        showToast(data.message, "error");
      }
    } catch (err) {
      showToast("Error saving entry", "error");
    }
  });

  // Render Table
  function renderKnowledgeBaseTable(kbEntries) {
    kbTableBody.innerHTML = "";
    if (!kbEntries || kbEntries.length === 0) {
      kbTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 20px; color:var(--text-secondary);">No entries in this dataset.</td></tr>`;
      return;
    }

    kbEntries.forEach(entry => {
      const tr = document.createElement("tr");
      const patternsText = Array.isArray(entry.patterns) ? entry.patterns.join(", ") : entry.patterns;
      const repliesText = Array.isArray(entry.quick_replies) ? entry.quick_replies.join(", ") : (entry.quick_replies || "-");

      tr.innerHTML = `
        <td>
          <span class="intent-badge-sm">${entry.intent || "intent"}</span>
          <div class="pattern-list-sm">${patternsText}</div>
        </td>
        <td style="white-space: pre-wrap; font-size: 0.8rem;">${entry.response}</td>
        <td><span style="color:var(--text-secondary); font-size:0.75rem;">${repliesText}</span></td>
        <td>
          <button class="del-btn" data-id="${entry.id}" title="Delete this entry">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      `;
      kbTableBody.appendChild(tr);
    });

    // Delete buttons
    kbTableBody.querySelectorAll(".del-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.id;
        if (confirm("Delete this knowledge entry from the bot?")) {
          try {
            const res = await fetch(`/api/dataset/entry/${id}`, { method: "DELETE" });
            const data = await res.json();
            if (data.status === "success") {
              showToast("Entry removed");
              btn.closest("tr").remove();
              // Update total count
              const curRes = await fetch("/api/dataset/current");
              const curData = await curRes.json();
              currentDataset = curData.dataset;
              drawerIntentsCount.textContent = currentDataset.total_intents;
            }
          } catch (err) {
            showToast("Error removing entry", "error");
          }
        }
      });
    });
  }

  // Filter Search
  kbSearchInput.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase();
    const rows = kbTableBody.querySelectorAll("tr");
    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(q) ? "" : "none";
    });
  });

  // Dataset File Upload
  datasetFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      showToast("Uploading dataset...", "success");
      const res = await fetch("/api/dataset/upload", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.status === "success") {
        showToast(data.message);
        currentDataset = data.summary;
        updateUIWithDataset(currentDataset);
        await loadPresetsList();
      } else {
        showToast(data.message || "Upload failed", "error");
      }
    } catch (err) {
      showToast("Error uploading dataset file", "error");
    }
  });

  // Export Dataset JSON
  exportDatasetBtn.addEventListener("click", () => {
    window.location.href = "/api/dataset/export";
  });

  // ---------------- CONNECT REAL WHATSAPP MODAL ----------------

  function openApiGuide() {
    apiGuideModal.classList.remove("hidden");
    // Update live webhook url
    const origin = window.location.origin;
    document.getElementById("metaWebhookUrlDisplay").textContent = `${origin}/webhook`;
  }

  function closeApiGuide() {
    apiGuideModal.classList.add("hidden");
  }

  openApiGuideBtn.addEventListener("click", openApiGuide);
  closeApiGuideBtn.addEventListener("click", closeApiGuide);
  closeApiGuideFooterBtn.addEventListener("click", closeApiGuide);

  apiGuideModal.addEventListener("click", (e) => {
    if (e.target === apiGuideModal) {
      closeApiGuide();
    }
  });

  // Guide Tabs (Meta vs Twilio)
  document.querySelectorAll(".guide-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".guide-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".guide-tab-content").forEach(c => c.classList.remove("active"));
      tab.classList.add("active");
      if (tab.dataset.guide === "meta") {
        document.getElementById("guideMeta").classList.add("active");
      } else {
        document.getElementById("guideTwilio").classList.add("active");
      }
    });
  });

  // Copy Buttons
  document.querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.copy;
      const text = document.getElementById(targetId).textContent;
      navigator.clipboard.writeText(text).then(() => {
        const original = btn.innerHTML;
        btn.innerHTML = `<i class="fa-solid fa-check"></i> Copied!`;
        btn.style.background = "var(--wa-green)";
        btn.style.color = "#fff";
        setTimeout(() => {
          btn.innerHTML = original;
          btn.style.background = "";
          btn.style.color = "";
        }, 2000);
      });
    });
  });

  // Kick off initial load
  loadInitialData();
});
