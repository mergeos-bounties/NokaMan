const API_BASE_KEY = "nokaman-api-base";
const SKILLS = ["vocabulary", "grammar", "reading", "writing", "listening", "speaking"];
const state = {
  busy: false,
};

const el = {
  apiForm: document.querySelector("#api-form"),
  apiBase: document.querySelector("#api-base"),
  apiStatus: document.querySelector("#api-status"),
  form: document.querySelector("#assessment-form"),
  language: document.querySelector("#language"),
  skill: document.querySelector("#skill"),
  text: document.querySelector("#text"),
  placementAnswers: document.querySelector("#placement-answers"),
  loadDemo: document.querySelector("#load-demo"),
  runPlacement: document.querySelector("#run-placement"),
  cefr: document.querySelector("#cefr"),
  score: document.querySelector("#score"),
  model: document.querySelector("#model"),
  radar: document.querySelector("#radar"),
  bands: document.querySelector("#bands"),
  details: document.querySelector("#details"),
  rawJson: document.querySelector("#raw-json"),
};

const savedBase = window.localStorage.getItem(API_BASE_KEY);
if (savedBase) {
  el.apiBase.value = savedBase;
}

el.apiForm.addEventListener("submit", (event) => {
  event.preventDefault();
  checkHealth();
});

el.form.addEventListener("submit", (event) => {
  event.preventDefault();
  assessText();
});

el.loadDemo.addEventListener("click", loadDemo);
el.runPlacement.addEventListener("click", runPlacement);

checkHealth(true);

function apiBase() {
  return el.apiBase.value.trim().replace(/\/+$/, "");
}

async function api(path, options = {}) {
  const base = apiBase();
  window.localStorage.setItem(API_BASE_KEY, base);
  const response = await fetch(`${base}${path}`, {
    headers: {
      "content-type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || response.statusText || "Request failed";
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail);
  }
  return payload;
}

async function checkHealth(loadDefault = false) {
  setStatus("Checking", "");
  try {
    const health = await api("/health");
    populateLanguages(health.languages || []);
    setStatus(`Connected ${health.version || ""}`.trim(), "ok");
    if (loadDefault) {
      await loadDemo();
    }
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function assessText() {
  const text = el.text.value.trim();
  if (!text) {
    setStatus("Enter learner text", "error");
    return;
  }
  await runRequest(async () => {
    const result = await api("/assess/text", {
      method: "POST",
      body: JSON.stringify({
        language: el.language.value,
        text,
        skill: el.skill.value,
      }),
    });
    renderResult(result);
  });
}

async function loadDemo() {
  await runRequest(async () => {
    const result = await api(`/assess/demo/${encodeURIComponent(el.language.value)}`);
    if (result.demo_text) {
      el.text.value = result.demo_text;
    }
    renderResult(result);
  });
}

async function runPlacement() {
  const answers = el.placementAnswers.value
    .split("\n")
    .map((answer) => answer.trim())
    .filter(Boolean);
  if (!answers.length) {
    setStatus("Enter placement answers", "error");
    return;
  }
  await runRequest(async () => {
    const result = await api("/assess/placement", {
      method: "POST",
      body: JSON.stringify({
        language: el.language.value,
        answers,
      }),
    });
    renderResult(result);
  });
}

async function runRequest(callback) {
  setBusy(true);
  setStatus("Running", "");
  try {
    await callback();
    setStatus("Ready", "ok");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    setBusy(false);
  }
}

function setBusy(isBusy) {
  state.busy = isBusy;
  for (const button of document.querySelectorAll("button")) {
    button.disabled = isBusy;
  }
}

function setStatus(message, kind) {
  el.apiStatus.textContent = message;
  el.apiStatus.className = `status ${kind}`.trim();
}

function populateLanguages(languages) {
  if (!languages.length) {
    return;
  }
  const current = el.language.value;
  const labels = new Map([
    ["en", "English"],
    ["ko", "Korean"],
    ["ja", "Japanese"],
    ["vi", "Vietnamese"],
    ["zh", "Chinese"],
    ["es", "Spanish"],
    ["fr", "French"],
    ["de", "German"],
  ]);
  el.language.replaceChildren(
    ...languages.map((code) => {
      const option = document.createElement("option");
      option.value = code;
      option.textContent = labels.get(code) || code.toUpperCase();
      return option;
    }),
  );
  el.language.value = languages.includes(current) ? current : languages[0];
}

function renderResult(result) {
  const score = result.overall ?? result.score ?? averageItemOverall(result.items);
  el.cefr.textContent = result.cefr || "-";
  el.score.textContent = Number.isFinite(score) ? Number(score).toFixed(2) : "-";
  el.model.textContent = result.model || modelFromItems(result.items) || "-";
  renderBands(result.framework_bands || {});
  renderDetails(result);
  renderRadar(skillScores(result));
  el.rawJson.textContent = JSON.stringify(result, null, 2);
}

function renderBands(bands) {
  el.bands.replaceChildren();
  const entries = Object.entries(bands);
  if (!entries.length) {
    el.bands.append(emptyText("No framework bands returned"));
    return;
  }
  for (const [name, value] of entries) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = `${humanize(name)} ${value}`;
    el.bands.append(chip);
  }
}

function renderDetails(result) {
  el.details.replaceChildren();
  const rows = [
    ["Language", result.language_name || result.language || "-"],
    ["Frameworks", Array.isArray(result.frameworks) ? result.frameworks.join(", ") : "-"],
    ["Skill", result.skill || "-"],
    ["Items", result.n_items || "-"],
    ["Features", result.features ? featureSummary(result.features) : "-"],
  ];
  for (const [label, value] of rows) {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = String(value);
    el.details.append(dt, dd);
  }
}

function renderRadar(scores) {
  el.radar.replaceChildren();
  const entries = SKILLS.map((skill) => [skill, scores[skill]]).filter(([, value]) =>
    Number.isFinite(value),
  );
  if (!entries.length) {
    el.radar.append(emptyText("Run demo or placement to see multi-skill scores"));
    return;
  }

  const size = 360;
  const center = size / 2;
  const radius = 122;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Skill radar chart");

  for (const level of [0.25, 0.5, 0.75, 1]) {
    svg.append(
      polygon(
        SKILLS.map((_, index) => point(index, level * radius, center)),
        "none",
        "#d8ddd3",
        "1",
      ),
    );
  }

  for (let index = 0; index < SKILLS.length; index += 1) {
    const end = point(index, radius, center);
    const axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
    axis.setAttribute("x1", center);
    axis.setAttribute("y1", center);
    axis.setAttribute("x2", end.x);
    axis.setAttribute("y2", end.y);
    axis.setAttribute("stroke", "#d8ddd3");
    svg.append(axis);

    const labelPoint = point(index, radius + 32, center);
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", labelPoint.x);
    text.setAttribute("y", labelPoint.y);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "middle");
    text.setAttribute("fill", "#20262e");
    text.setAttribute("font-size", "12");
    text.textContent = humanize(SKILLS[index]);
    svg.append(text);
  }

  const skillMap = Object.fromEntries(entries);
  const dataPoints = SKILLS.map((skill, index) => {
    const value = Math.max(0, Math.min(100, skillMap[skill] || 0));
    return point(index, (value / 100) * radius, center);
  });
  svg.append(polygon(dataPoints, "rgba(43, 122, 120, 0.26)", "#2b7a78", "3"));

  for (const [skill, value] of entries) {
    const row = document.createElementNS("http://www.w3.org/2000/svg", "title");
    row.textContent = `${humanize(skill)}: ${Number(value).toFixed(2)}`;
    svg.append(row);
  }

  el.radar.append(svg);
}

function polygon(points, fill, stroke, width) {
  const shape = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
  shape.setAttribute("points", points.map((item) => `${item.x},${item.y}`).join(" "));
  shape.setAttribute("fill", fill);
  shape.setAttribute("stroke", stroke);
  shape.setAttribute("stroke-width", width);
  return shape;
}

function point(index, radius, center) {
  const angle = -Math.PI / 2 + (index * Math.PI * 2) / SKILLS.length;
  return {
    x: Number((center + Math.cos(angle) * radius).toFixed(3)),
    y: Number((center + Math.sin(angle) * radius).toFixed(3)),
  };
}

function skillScores(result) {
  if (result.skills) {
    return result.skills;
  }
  if (Array.isArray(result.items) && result.items.length) {
    const totals = {};
    for (const item of result.items) {
      for (const [skill, value] of Object.entries(item.skills || {})) {
        totals[skill] = (totals[skill] || 0) + Number(value || 0);
      }
    }
    return Object.fromEntries(
      Object.entries(totals).map(([skill, total]) => [skill, total / result.items.length]),
    );
  }
  if (result.skill && Number.isFinite(result.score)) {
    return { [result.skill]: result.score };
  }
  return {};
}

function averageItemOverall(items) {
  if (!Array.isArray(items) || !items.length) {
    return undefined;
  }
  const values = items.map((item) => item.overall).filter((value) => Number.isFinite(value));
  if (!values.length) {
    return undefined;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function modelFromItems(items) {
  if (!Array.isArray(items)) {
    return undefined;
  }
  return items.find((item) => item.model)?.model;
}

function featureSummary(features) {
  return Object.entries(features)
    .map(([key, value]) => `${humanize(key)}: ${value}`)
    .join(", ");
}

function humanize(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function emptyText(message) {
  const item = document.createElement("p");
  item.className = "empty";
  item.textContent = message;
  return item;
}
