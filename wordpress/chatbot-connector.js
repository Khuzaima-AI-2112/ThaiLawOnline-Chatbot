/**
 * ThaiLawOnline Chatbot Connector
 *
 * Intercepts chat widget messages and routes them through the WordPress AJAX
 * proxy to the LLM Council backend. Works with most chat widget plugins that
 * expose a message input and display area, or can be used standalone.
 */
(function () {
  "use strict";

  // Session ID persists across messages in the same page visit
  let sessionId = "";

  /**
   * Send a message to the chatbot backend via WordPress AJAX.
   *
   * @param {string} message - The user's question
   * @returns {Promise<object>} - The chatbot response
   */
  async function sendMessage(message) {
    const formData = new FormData();
    formData.append("action", "thailaw_chat");
    formData.append("nonce", ThaiLawChatbot.nonce);
    formData.append("message", message);
    formData.append("session_id", sessionId);

    const response = await fetch(ThaiLawChatbot.ajaxUrl, {
      method: "POST",
      credentials: "same-origin",
      body: formData,
    });

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.data?.message || "Failed to get response");
    }

    // Update session ID for subsequent messages
    if (result.data.session_id) {
      sessionId = result.data.session_id;
    }

    return result.data;
  }

  /**
   * Format source citations as HTML.
   *
   * @param {Array} sources - Array of {source, excerpt} objects
   * @returns {string} - HTML string
   */
  function formatSources(sources) {
    if (!sources || sources.length === 0) return "";

    const items = sources
      .map(
        (s) =>
          `<li><strong>${escapeHtml(s.source)}</strong>: ${escapeHtml(s.excerpt)}</li>`
      )
      .join("");

    return `<details class="thailaw-sources"><summary>Sources (${sources.length})</summary><ul>${items}</ul></details>`;
  }

  /**
   * Escape HTML entities.
   */
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // ============================================================
  // Chat Widget Integration
  // ============================================================

  /**
   * Initialize the chatbot connector.
   * Looks for a chat widget or creates a minimal chat interface.
   */
  function init() {
    // Try to find an existing chat widget input
    const chatInput =
      document.querySelector('[data-thailaw-input]') ||
      document.querySelector(".chat-widget-input") ||
      document.querySelector("#chat-input");

    const chatMessages =
      document.querySelector('[data-thailaw-messages]') ||
      document.querySelector(".chat-widget-messages") ||
      document.querySelector("#chat-messages");

    if (!chatInput || !chatMessages) {
      // No existing chat widget found — skip initialization.
      // The chat widget plugin should provide the UI.
      console.log(
        "ThaiLaw Chatbot: No chat widget found. Add data-thailaw-input and data-thailaw-messages attributes to your chat elements."
      );
      return;
    }

    // Handle message submission
    chatInput.addEventListener("keydown", async function (e) {
      if (e.key !== "Enter" || e.shiftKey) return;
      e.preventDefault();

      const message = chatInput.value.trim();
      if (!message) return;

      // Show user message
      appendMessage(chatMessages, "user", message);
      chatInput.value = "";
      chatInput.disabled = true;

      // Show loading indicator
      const loadingEl = appendMessage(
        chatMessages,
        "assistant",
        "กำลังปรึกษาผู้เชี่ยวชาญกฎหมาย..."
      );

      try {
        const data = await sendMessage(message);

        // Replace loading with actual response
        loadingEl.innerHTML = formatAnswer(data.answer, data.sources);
      } catch (err) {
        loadingEl.innerHTML = `<span class="thailaw-error">ขออภัย เกิดข้อผิดพลาด: ${escapeHtml(err.message)}</span>`;
      } finally {
        chatInput.disabled = false;
        chatInput.focus();
      }
    });
  }

  /**
   * Append a message to the chat display.
   */
  function appendMessage(container, role, text) {
    const div = document.createElement("div");
    div.className = `thailaw-message thailaw-${role}`;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  /**
   * Format the final answer with optional sources.
   */
  function formatAnswer(answer, sources) {
    return `<div class="thailaw-answer">${escapeHtml(answer)}</div>${formatSources(sources)}`;
  }

  // Expose sendMessage globally for custom integrations
  window.ThaiLawChatbotAPI = { sendMessage, formatSources };

  // Initialize when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
