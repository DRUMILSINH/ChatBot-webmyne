let savedUserName = "You"; // Global fallback

function showTypingIndicator() {
  const indicator = document.getElementById("typing-indicator");
  if (indicator) indicator.style.display = "block";
}

function hideTypingIndicator() {
  const indicator = document.getElementById("typing-indicator");
  if (indicator) indicator.style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
  // 1. Load user's name from session
  fetch("/chat/get-user-name/")
    .then(res => res.json())
    .then(data => {
      if (data.name) {
        savedUserName = data.name;

        document.getElementById("user-name").value = data.name || "";
        document.getElementById("user-email").value = data.email || "";
        document.getElementById("user-phone").value = data.phone || "";
      }
    })
    .catch(() => {
      console.warn("Could not fetch saved name.");
    });

  // Show/hide user info form
  document.getElementById("open-user-form").addEventListener("click", () => {
    document.getElementById("user-info-box").style.display = "block";
document.getElementById("user-info-status").style.display = "none";
  });

  document.getElementById("close-user-form").addEventListener("click", () => {
    document.getElementById("user-info-box").style.display = "none";
  });

  // 2. Handle chatbot message send
  document.getElementById("chat-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const input = document.getElementById("user-input");
    const message = input.value.trim();

    if (!message) {
      hideTypingIndicator();
      return;
    }

    addMessage("You", message);
    input.value = "";

    showTypingIndicator();

    try {
      const vectorId = "webmyne";
      const response = await fetch("/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: message, vector_id: vectorId }),
      });

      const data = await response.json();
      const reply = data.answer || data.error || "Something went wrong!";
      addMessage("AI agent", reply);
    } catch (err) {
      addMessage("AI agent", "Error fetching response.");
    } finally {
      hideTypingIndicator();
    }
  });


document.getElementById("user-info-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const nameField = document.getElementById("user-name");
  const emailField = document.getElementById("user-email");
  const phoneField = document.getElementById("user-phone");
  const statusEl = document.getElementById("user-info-status");

  const name = nameField.value.trim();
  const email = emailField.value.trim();
  const phone = phoneField.value.trim();

  // Always hide before save
  statusEl.style.display = "none";

  try {
    const response = await fetch("/chat/save-user-info/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ name, email, phone })
    });

    const result = await response.json();

    //  THIS matches your backend
    if (response.ok) {if (result.name) {
    savedUserName = result.name;
  }


      nameField.value = "";
      emailField.value = "";
      phoneField.value = "";

      statusEl.textContent = " Info saved!";
      statusEl.style.display = "inline";

      setTimeout(() => {
        statusEl.style.display = "none";
      }, 5000);
    } else {
      statusEl.textContent = " Failed to save";
      statusEl.style.display = "inline";
    }

  } catch (err) {
    console.error("Failed to save user info", err);
    statusEl.textContent = " Failed to save";
    statusEl.style.display = "inline";
  }
});

  //  4. Show welcome message on load
  addMessage(
    "AI agent",
    "👋 Hi there! I'm your assistant. Please share your details and feel free to ask about our company!"
  );
});

//  5. Append message to chat window
function addMessage(sender, message) {
  const box = document.getElementById("chat-box");
  const msg = document.createElement("div");

  msg.classList.add("chat-message");

  if (sender === "AI agent") {
    msg.classList.add("ai-message");
  } else {
    msg.classList.add("human-message");
  }

  let messageHTML = "";

  if (sender === "AI agent") {
    if (typeof message === "object" && message.answer) {
      let answerHTML = marked.parse(message.answer || "");
      answerHTML = answerHTML.replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" ');

      let sourcesHTML = "";
      if (Array.isArray(message.sources) && message.sources.length > 0) {
        sourcesHTML += `<hr><strong>Sources</strong><ul>`;
        message.sources.forEach((src) => {
          const url = src.url || "N/A";
          const note = src.note || "✓ Verified (Crawled)";
          let badge = "";

          if (note.includes("not yet crawled")) {
            badge = `<span style="color: orange;"> ${note}</span>`;
          } else if (note.includes("not discovered")) {
            badge = `<span style="color: red;">${note}</span>`;
          } else {
            badge = `<span style="color: green;"> ${note}</span>`;
          }

          sourcesHTML += `<li><a href="${url}" target="_blank">${url}</a><br>${badge}</li>`;
        });
        sourcesHTML += `</ul>`;
      }

      messageHTML = `<p>${answerHTML}</p>${sourcesHTML}`;
    } else {
      let parsed = marked.parse(message || "");
      messageHTML = parsed.replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" ');
    }
  } else {
    messageHTML = `<p>${message}</p>`;
  }

  const displayName = sender === "You" ? savedUserName : "AI agent";
  msg.innerHTML = `<strong>${displayName}</strong> ${messageHTML}`;

  box.appendChild(msg);
  box.scrollTop = box.scrollHeight;

  attachClickLogger();
}

//  6. Log clicks on URLs in chat
function attachClickLogger() {
  const links = document.querySelectorAll("#chat-box a");
  links.forEach(link => {
    link.addEventListener("click", async (e) => {
      const clickedURL = e.currentTarget.href;
      try {
        await fetch("/chat/log-click/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ url: clickedURL })
        });
      } catch (err) {
        console.error("Failed to log clicked URL", err);
      }
    });
  });
}




