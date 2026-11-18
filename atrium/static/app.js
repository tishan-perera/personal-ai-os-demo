const FLAG_LABELS = {
  sent_messages: "Simulated mail sent",
  studio_rent: "Studio rent",
  post: "Post",
  application: "Application",
  reminder: "Reminder",
};

const DEMO_RUNS = {
  budget: "How does the November household budget look?",
  queue: "Draft a reply to the landlord about the leak, and send it",
  audit: "Pay the fictional studio rent of 900 dollars",
};

const state = {
  busy: false,
  data: null,
};

const rosterEl = document.querySelector("#roster");
const threadEl = document.querySelector("#thread");
const promptsEl = document.querySelector("#prompts");
const proposalsEl = document.querySelector("#proposals");
const auditEl = document.querySelector("#audit");
const flagsEl = document.querySelector("#flags");
const modeEl = document.querySelector("#mode");
const errorEl = document.querySelector("#error");
const formEl = document.querySelector("#composer");
const requestEl = document.querySelector("#request");
const askEl = document.querySelector("#ask");

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  void ask(requestEl.value);
});

document.querySelector("#reset").addEventListener("click", () => {
  void resetDemo();
});

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function showError(message) {
  errorEl.textContent = message || "";
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  let payload = {};
  try {
    payload = await response.json();
  } catch (_error) {
    payload = {};
  }
  if (!response.ok) {
    const message = payload.error && payload.error.message
      ? payload.error.message
      : "The desk could not complete that.";
    throw new Error(message);
  }
  return payload;
}

async function refresh() {
  const response = await fetch("/api/state");
  if (!response.ok) {
    throw new Error("The desk could not load its state.");
  }
  state.data = await response.json();
  render();
}

function render() {
  const data = state.data;
  modeEl.textContent = data.llm_enabled ? "Optional model on" : "Deterministic demo";
  const pending = data.proposals.filter((item) => item.status === "pending").length;
  const queueTitle = pending ? `Approval queue · ${pending} waiting` : "Approval queue";
  document.querySelector(".gate-head h2").textContent = queueTitle;
  const active = data.turns.length ? data.turns[data.turns.length - 1].seat_id : "chief";
  rosterEl.innerHTML = data.roster.map((seat) => {
    const current = seat.id === active ? " active" : "";
    return (
      `<article class="seat${current}">` +
      `<p class="dept">${escapeHtml(seat.department)}</p>` +
      `<h3>${escapeHtml(seat.name)}</h3>` +
      `<p class="title">${escapeHtml(seat.title)}</p>` +
      `<p class="mandate">${escapeHtml(seat.mandate)}</p>` +
      "</article>"
    );
  }).join("");

  if (!data.turns.length) {
    threadEl.innerHTML = (
      '<p class="empty"><strong>Mara Quinn is the only front door.</strong> ' +
      "Ask in plain language. She hands the request to Mail, Finance, Content, Career, or Ops. " +
      "If two desks match, she keeps it. Sending, paying, publishing, submitting, and notifying " +
      "wait in Needs you until you approve.</p>"
    );
  } else {
    threadEl.innerHTML = data.turns.map((turn) => (
      '<article class="turn">' +
      `<p class="ask-line">You · ${escapeHtml(turn.request)}</p>` +
      '<div class="bubble">' +
      `<p class="who">${escapeHtml(turn.department)} · ${escapeHtml(turn.seat_name)}</p>` +
      `<p class="reason">${escapeHtml(turn.reason)} ` +
      `<span class="mode-tag">${escapeHtml(turn.mode)}</span></p>` +
      `<p class="reply">${escapeHtml(replyBody(turn))}</p>` +
      "</div></article>"
    )).join("");
    const last = threadEl.lastElementChild;
    if (last) {
      const box = last.getBoundingClientRect();
      const frame = threadEl.getBoundingClientRect();
      if (box.bottom > frame.bottom || box.top < frame.top) {
        last.scrollIntoView({ block: "nearest" });
      }
    }
  }

  promptsEl.innerHTML = data.prompts.map((prompt) => (
    `<button type="button" data-prompt="${escapeHtml(prompt.text)}">${escapeHtml(prompt.label)}</button>`
  )).join("");
  promptsEl.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      requestEl.value = button.dataset.prompt || "";
      void ask(requestEl.value);
    });
  });

  if (!data.proposals.length) {
    proposalsEl.innerHTML = (
      '<p class="quiet">Nothing is waiting. Consequential requests land here. ' +
      "Read-only questions never do.</p>"
    );
  } else {
    proposalsEl.innerHTML = data.proposals.map(renderProposal).join("");
    proposalsEl.querySelectorAll("button[data-decision]").forEach((button) => {
      button.addEventListener("click", () => {
        void decide(button.dataset.id, button.dataset.decision);
      });
    });
  }

  if (!data.audit.length) {
    auditEl.innerHTML = "<li>No events yet. A request will write the first line.</li>";
  } else {
    auditEl.innerHTML = data.audit.map((event) => (
      "<li>" +
      `<span class="kind">${escapeHtml(event.kind)}</span> ` +
      `${escapeHtml(event.summary)}` +
      "</li>"
    )).join("");
  }

  const flags = data.world.flags;
  flagsEl.innerHTML = Object.keys(FLAG_LABELS).map((key) => (
    `<dt>${escapeHtml(FLAG_LABELS[key])}</dt><dd>${escapeHtml(flags[key])}</dd>`
  )).join("");
}

function replyBody(turn) {
  const prefix = `${turn.seat_name} · ${turn.department}`;
  const lines = String(turn.reply).split("\n");
  if (lines[0] === prefix) {
    return lines.slice(1).join("\n").replace(/^\n/, "");
  }
  return turn.reply;
}

function renderProposal(proposal) {
  const riskClass = proposal.risk === "high" ? "pill high" : "pill";
  let footer = "";
  if (proposal.status === "pending") {
    footer = (
      '<div class="actions">' +
      `<button class="approve" type="button" data-id="${escapeHtml(proposal.id)}" data-decision="approve">Approve</button>` +
      `<button class="reject" type="button" data-id="${escapeHtml(proposal.id)}" data-decision="reject">Reject</button>` +
      "</div>"
    );
  } else if (proposal.status === "executed") {
    const notice = proposal.execution && proposal.execution.notice
      ? proposal.execution.notice
      : "Simulated.";
    footer = `<p class="stamp">Approved by ${escapeHtml(proposal.decided_by)}. ${escapeHtml(notice)}</p>`;
  } else if (proposal.status === "rejected") {
    footer = `<p class="stamp">Rejected by ${escapeHtml(proposal.decided_by)}. No-op. Nothing ran.</p>`;
  }
  return (
    `<article class="ticket ${escapeHtml(proposal.status)}">` +
    '<div class="ticket-top">' +
    `<span class="meta">${escapeHtml(proposal.id)} · ${escapeHtml(proposal.department)} · ${escapeHtml(proposal.seat_name)}</span>` +
    `<span class="${riskClass}">${escapeHtml(proposal.risk)} risk</span>` +
    "</div>" +
    `<h3>${escapeHtml(proposal.summary)}</h3>` +
    `<p class="detail">${escapeHtml(proposal.detail)}</p>` +
    '<p class="excerpt"><span>Untrusted request text. Stored, not executed.</span>' +
    `${escapeHtml(proposal.request_excerpt)}</p>` +
    footer +
    "</article>"
  );
}

async function ask(text) {
  const cleaned = text.trim();
  if (!cleaned || state.busy) {
    return;
  }
  state.busy = true;
  askEl.disabled = true;
  showError("");
  try {
    await postJson("/api/requests", { text: cleaned });
    requestEl.value = "";
    await refresh();
  } catch (error) {
    showError(error.message);
  } finally {
    state.busy = false;
    askEl.disabled = false;
  }
}

async function decide(id, decision) {
  if (state.busy) {
    return;
  }
  state.busy = true;
  showError("");
  try {
    await postJson(`/api/proposals/${id}/decision`, { decision, actor: "owner" });
    await refresh();
  } catch (error) {
    showError(error.message);
  } finally {
    state.busy = false;
  }
}

async function resetDemo() {
  if (state.busy) {
    return;
  }
  state.busy = true;
  showError("");
  try {
    state.data = await postJson("/api/reset", {});
    render();
  } catch (error) {
    showError(error.message);
  } finally {
    state.busy = false;
  }
}

async function boot() {
  const script = new URLSearchParams(location.search).get("demo");
  try {
    if (script === "audit") {
      const created = await postJson("/api/requests", { text: DEMO_RUNS.audit });
      await postJson(`/api/proposals/${created.proposal.id}/decision`, {
        decision: "approve",
        actor: "owner",
      });
    } else if (Object.prototype.hasOwnProperty.call(DEMO_RUNS, script)) {
      await postJson("/api/requests", { text: DEMO_RUNS[script] });
    }
    await refresh();
  } catch (error) {
    showError(error.message);
  } finally {
    document.body.dataset.ready = "true";
  }
}

void boot();
