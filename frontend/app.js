// --- In-memory mock data (no backend yet) ---

let nextTeamId = 1;
let nextMatchId = 1;

function makeTeam(name) {
  return { id: nextTeamId++, name };
}

function makeMatch(homeTeamId, awayTeamId, homeScore, awayScore, date, matchday) {
  return { id: nextMatchId++, homeTeamId, awayTeamId, homeScore, awayScore, date, matchday };
}

const teams = [
  makeTeam("Riverside FC"),
  makeTeam("Oakwood United"),
  makeTeam("Harbor City"),
  makeTeam("Westside Rangers"),
  makeTeam("Sunset Athletic"),
  makeTeam("Iron Bridge"), // no matches yet - should show zeroed stats
];

const [riverside, oakwood, harbor, westside, sunset] = teams;

const matches = [
  makeMatch(riverside.id, oakwood.id, 3, 1, "2026-08-02", 1),
  makeMatch(harbor.id, westside.id, 2, 2, "2026-08-02", 1),
  makeMatch(sunset.id, riverside.id, 0, 1, "2026-08-02", 1),

  makeMatch(oakwood.id, harbor.id, 1, 1, "2026-08-09", 2),
  makeMatch(westside.id, sunset.id, 3, 0, "2026-08-09", 2),
  makeMatch(riverside.id, westside.id, 2, 0, "2026-08-09", 2),

  makeMatch(harbor.id, riverside.id, 1, 4, "2026-08-16", 3),
  makeMatch(sunset.id, oakwood.id, 2, 2, "2026-08-16", 3),
  makeMatch(westside.id, oakwood.id, 1, 3, "2026-08-23", 3),
];

// --- Standings calculation ---

function computeStandings() {
  const stats = new Map();
  for (const team of teams) {
    stats.set(team.id, { team, played: 0, won: 0, drawn: 0, lost: 0, points: 0 });
  }

  for (const match of matches) {
    const home = stats.get(match.homeTeamId);
    const away = stats.get(match.awayTeamId);
    if (!home || !away) continue;

    home.played++;
    away.played++;

    if (match.homeScore > match.awayScore) {
      home.won++;
      home.points += 3;
      away.lost++;
    } else if (match.homeScore < match.awayScore) {
      away.won++;
      away.points += 3;
      home.lost++;
    } else {
      home.drawn++;
      away.drawn++;
      home.points += 1;
      away.points += 1;
    }
  }

  return Array.from(stats.values()).sort((a, b) => b.points - a.points);
}

// --- Rendering ---

function renderStandings() {
  const tbody = document.getElementById("standings-body");
  const standings = computeStandings();

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

  const options = teams
    .map((team) => `<option value="${team.id}">${escapeHtml(team.name)}</option>`)
    .join("");

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

document.getElementById("add-team-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.getElementById("team-name");
  const name = input.value.trim();

  if (!name) {
    showMessage("add-team-message", "Please enter a team name.", "error");
    return;
  }
  if (teams.some((t) => t.name.toLowerCase() === name.toLowerCase())) {
    showMessage("add-team-message", "A team with that name already exists.", "error");
    return;
  }

  teams.push(makeTeam(name));
  input.value = "";
  renderAll();
  showMessage("add-team-message", `Added "${name}".`, "success");
});

document.getElementById("record-match-form").addEventListener("submit", (event) => {
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
  if (Number.isNaN(homeScore) || Number.isNaN(awayScore) || homeScore < 0 || awayScore < 0) {
    showMessage("record-match-message", "Please enter valid, non-negative scores.", "error");
    return;
  }
  if (!date) {
    showMessage("record-match-message", "Please enter a date.", "error");
    return;
  }
  if (!matchday || matchday < 1) {
    showMessage("record-match-message", "Please enter a valid matchday number.", "error");
    return;
  }

  matches.push(makeMatch(homeTeamId, awayTeamId, homeScore, awayScore, date, matchday));
  event.target.reset();
  renderAll();
  showMessage("record-match-message", "Match recorded.", "success");
});

// --- Init ---

renderAll();
