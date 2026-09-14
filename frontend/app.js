// Talks to the FastAPI backend defined in openapi.yaml. No local mock data
// or client-side standings calculation any more - the backend is the
// source of truth.

const API_BASE = "http://localhost:8000/api";

let teams = [];
let matches = [];
let standings = [];

// --- API helpers ---

async function apiRequest(path, options) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch (networkError) {
    throw new ApiError(
      `Could not reach the backend at ${API_BASE}. Is it running?`,
      0
    );
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body && body.detail) detail = body.detail;
    } catch (_) {
      // response body wasn't JSON - fall back to the generic message
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) return null;
  return response.json();
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function apiGet(path) {
  return apiRequest(path);
}

function apiPost(path, body) {
  return apiRequest(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// --- Loading data from the backend ---

async function loadAll() {
  try {
    const [teamsData, matchesData, standingsData] = await Promise.all([
      apiGet("/teams"),
      apiGet("/matches"),
      apiGet("/standings"),
    ]);
    teams = teamsData;
    matches = matchesData;
    standings = standingsData;
    hideConnectionBanner();
  } catch (err) {
    teams = [];
    matches = [];
    standings = [];
    showConnectionBanner(err.message);
  }
  renderAll();
}

function showConnectionBanner(message) {
  const banner = document.getElementById("connection-banner");
  banner.textContent = message;
  banner.hidden = false;
}

function hideConnectionBanner() {
  const banner = document.getElementById("connection-banner");
  banner.hidden = true;
  banner.textContent = "";
}

// --- Rendering ---

function renderStandings() {
  const tbody = document.getElementById("standings-body");

  if (standings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No teams yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = "";
  standings.forEach((row, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td class="team-col">${escapeHtml(row.team.name)}</td>
      <td>${row.played}</td>
      <td>${row.won}</td>
      <td>${row.drawn}</td>
      <td>${row.lost}</td>
      <td>${row.points}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderTeamSelects() {
  const homeSelect = document.getElementById("home-team");
  const awaySelect = document.getElementById("away-team");
  const previousHome = homeSelect.value;
  const previousAway = awaySelect.value;

  const options = teams.length
    ? teams.map((team) => `<option value="${team.id}">${escapeHtml(team.name)}</option>`).join("")
    : `<option value="" disabled selected>Add a team first</option>`;

  homeSelect.innerHTML = options;
  awaySelect.innerHTML = options;

  if (previousHome) homeSelect.value = previousHome;
  if (previousAway) awaySelect.value = previousAway;
}

function renderMatches() {
  const tbody = document.getElementById("matches-body");
  const teamById = new Map(teams.map((t) => [t.id, t]));

  const sorted = [...matches].sort((a, b) => {
    if (a.matchday !== b.matchday) return b.matchday - a.matchday;
    return b.date.localeCompare(a.date);
  });

  if (sorted.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No matches recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = "";
  for (const match of sorted) {
    const home = teamById.get(match.homeTeamId);
    const away = teamById.get(match.awayTeamId);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${match.matchday}</td>
      <td>${formatDate(match.date)}</td>
      <td class="team-col">${escapeHtml(home ? home.name : "Unknown")}</td>
      <td>${match.homeScore} – ${match.awayScore}</td>
      <td class="team-col">${escapeHtml(away ? away.name : "Unknown")}</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderAll() {
  renderStandings();
  renderTeamSelects();
  renderMatches();
}

// --- Helpers ---

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(isoDate) {
  const d = new Date(isoDate + "T00:00:00");
  if (isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function showMessage(elementId, text, type) {
  const el = document.getElementById(elementId);
  el.textContent = text;
  el.className = "form-message " + (type || "");
  if (text) {
    setTimeout(() => {
      el.textContent = "";
      el.className = "form-message";
    }, 3000);
  }
}

// --- Form handlers ---

document.getElementById("add-team-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("team-name");
  const name = input.value.trim();

  if (!name) {
    showMessage("add-team-message", "Please enter a team name.", "error");
    return;
  }

  try {
    await apiPost("/teams", { name });
    input.value = "";
    await loadAll();
    showMessage("add-team-message", `Added "${name}".`, "success");
  } catch (err) {
    showMessage("add-team-message", err.message, "error");
  }
});

document.getElementById("record-match-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const homeTeamId = Number(document.getElementById("home-team").value);
  const awayTeamId = Number(document.getElementById("away-team").value);
  const homeScore = Number(document.getElementById("home-score").value);
  const awayScore = Number(document.getElementById("away-score").value);
  const date = document.getElementById("match-date").value;
  const matchday = Number(document.getElementById("matchday").value);

  if (!homeTeamId || !awayTeamId) {
    showMessage("record-match-message", "Please select both teams.", "error");
    return;
  }
  if (homeTeamId === awayTeamId) {
    showMessage("record-match-message", "Home and away teams must be different.", "error");
    return;
  }
  if (!date) {
    showMessage("record-match-message", "Please enter a date.", "error");
    return;
  }

  try {
    await apiPost("/matches", {
      homeTeamId,
      awayTeamId,
      homeScore,
      awayScore,
      date,
      matchday,
    });
    event.target.reset();
    await loadAll();
    showMessage("record-match-message", "Match recorded.", "success");
  } catch (err) {
    showMessage("record-match-message", err.message, "error");
  }
});

// --- Init ---

loadAll();
