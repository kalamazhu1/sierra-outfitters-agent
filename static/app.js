const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const resetButton = document.querySelector("#resetButton");
const suggestionButtons = document.querySelectorAll("[data-prompt]");

let isSending = false;

function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "You" : "SO";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.append(...formatText(text));

  article.append(avatar, bubble);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function formatText(text) {
  const nodes = [];
  const urlPattern = /(https?:\/\/[^\s)]+)/g;
  const boldPattern = /\*\*([^*]+)\*\*/g;
  const paragraphs = text.split(/\n{2,}/);

  paragraphs.forEach((paragraph, paragraphIndex) => {
    if (paragraphIndex > 0) {
      nodes.push(document.createElement("br"));
    }

    paragraph.split("\n").forEach((line, lineIndex) => {
      if (lineIndex > 0) {
        nodes.push(document.createElement("br"));
      }

      let lastIndex = 0;
      for (const match of line.matchAll(urlPattern)) {
        if (match.index > lastIndex) {
          nodes.push(...formatInlineText(line.slice(lastIndex, match.index), boldPattern));
        }

        const link = document.createElement("a");
        link.href = match[0];
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = match[0];
        nodes.push(link);
        lastIndex = match.index + match[0].length;
      }

      if (lastIndex < line.length) {
        nodes.push(...formatInlineText(line.slice(lastIndex), boldPattern));
      }
    });
  });

  return nodes;
}

function formatInlineText(text, boldPattern) {
  const nodes = [];
  let lastIndex = 0;

  for (const match of text.matchAll(boldPattern)) {
    if (match.index > lastIndex) {
      nodes.push(document.createTextNode(text.slice(lastIndex, match.index)));
    }

    const strong = document.createElement("strong");
    strong.textContent = match[1];
    nodes.push(strong);
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    nodes.push(document.createTextNode(text.slice(lastIndex)));
  }

  return nodes;
}

function setSending(nextValue) {
  isSending = nextValue;
  input.disabled = nextValue;
  form.querySelector("button").disabled = nextValue;
}

async function sendMessage(message) {
  if (!message || isSending) return;

  appendMessage("user", message);
  input.value = "";
  input.style.height = "auto";
  setSending(true);

  const pending = appendMessage("bot", "Finding the best trail...");
  pending.classList.add("pending");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();

    pending.remove();
    appendMessage("bot", data.ok ? data.reply : `I hit a snag on the trail: ${data.error}`);
  } catch (error) {
    pending.remove();
    appendMessage("bot", "I hit a snag on the trail: the local chat server did not respond.");
  } finally {
    setSending(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value.trim());
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    sendMessage(button.dataset.prompt);
  });
});

resetButton.addEventListener("click", async () => {
  await fetch("/api/reset", { method: "POST" });
  messages.innerHTML = "";
  appendMessage(
    "bot",
    "Fresh trail, fresh chat. I can help with orders, tracking, product recommendations, and the Early Risers Promotion."
  );
  input.focus();
});
