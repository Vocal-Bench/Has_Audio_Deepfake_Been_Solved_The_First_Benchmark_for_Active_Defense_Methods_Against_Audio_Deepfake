const state = {
  activeAudio: null,
  activeButton: null,
  activeBranch: null,
  activeVariant: null,
  pipeline: null,
};

const els = {
  root: document.querySelector("#app"),
};

const PIPELINE_URL = document.body.dataset.pipelineUrl || "./demo_assets/pipeline.json";
const SUMMARY_URL = document.body.dataset.summaryUrl || "./demo_assets/results_summary.json";

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => (
    {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char]
  ));
}

function formatSeconds(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "";
  }
  return `${Number(value).toFixed(2)} s`;
}

function playButton(src, label) {
  const safeSrc = escapeHtml(src || "");
  const safeLabel = escapeHtml(label);
  return `<button class="play-orb" type="button" data-audio-src="${safeSrc}" aria-label="Play ${safeLabel}">▶</button>`;
}

function renderLegendItem(item) {
  return `
    <div class="legend-item">
      <div class="legend-term">${escapeHtml(item.label)}</div>
      <div class="legend-desc">${escapeHtml(item.description)}</div>
    </div>
  `;
}

function renderLeaf(leaf) {
  return `
    <div class="leaf-node ${leaf.kind.toLowerCase()}">
      ${playButton(leaf.audio, leaf.model)}
      <div class="leaf-text">
        <div class="leaf-model">${escapeHtml(leaf.model)}</div>
        <div class="leaf-kind">${escapeHtml(leaf.kind)}</div>
      </div>
    </div>
  `;
}

function renderVariantPopover(variant) {
  const ttsLeaves = variant.leaves.filter((leaf) => leaf.kind === "TTS");
  const vcLeaves = variant.leaves.filter((leaf) => leaf.kind === "VC");
  return `
    <div class="variant-popover">
      <div class="popover-head">
        <div>
          <div class="popover-title">${escapeHtml(variant.label)}</div>
          <div class="popover-meta">${variant.tts_count} TTS · ${variant.vc_count} VC</div>
        </div>
        ${playButton(variant.audio, variant.label)}
      </div>
      <p class="popover-note">${escapeHtml(variant.note || "")}</p>
      <div class="popover-groups">
        <div class="popover-group">
          <div class="group-label">TTS</div>
          <div class="leaf-grid">
            ${ttsLeaves.map(renderLeaf).join("")}
          </div>
        </div>
        <div class="popover-group">
          <div class="group-label">VC</div>
          <div class="leaf-grid vc-grid">
            ${vcLeaves.map(renderLeaf).join("")}
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderVariantPill(variant, branchIndex) {
  const pillLabel = variant.badge || variant.label;
  return `
    <div class="variant-pill-wrap" data-variant-id="${branchIndex}:${variant.key}">
      <button class="variant-pill" type="button">${escapeHtml(pillLabel)}</button>
      ${renderVariantPopover(variant)}
    </div>
  `;
}

function renderBranch(branch, index) {
  return `
    <div class="branch-row" data-branch-index="${index}">
      <div class="defense-card" data-connect-id="defense-${index}">
        <div class="defense-head">
          ${playButton(branch.protected_audio, branch.group)}
          <div>
            <div class="defense-name">${escapeHtml(branch.group)}</div>
            <div class="defense-note">${escapeHtml(branch.note || "")}</div>
          </div>
        </div>
      </div>
      <div class="variant-rail">
        ${branch.variants.map((variant) => renderVariantPill(variant, index)).join("")}
      </div>
    </div>
  `;
}

function renderHero(payload) {
  const sampleMeta = [
    payload.sample.lang_label,
    payload.sample.task_label,
    formatSeconds(payload.sample.duration),
  ].filter(Boolean).join(" · ");
  const transcript = payload.sample.transcript
    ? `<p class="sample-transcript">${escapeHtml(payload.sample.transcript)}</p>`
    : "";

  return `
    <section class="hero">
      <div class="hero-main">
        <div class="eyebrow">Static Audio Explorer</div>
        <h1>${escapeHtml(payload.title || "VocalBench Demo")}</h1>
        <p class="hero-copy">${escapeHtml(payload.subtitle || "")}</p>
        <div class="stat-row">
          <div class="stat-chip"><span>Defenses</span><strong>${payload.meta.defense_count}</strong></div>
          <div class="stat-chip"><span>TTS Models</span><strong>${payload.meta.tts_count}</strong></div>
          <div class="stat-chip"><span>VC Models</span><strong>${payload.meta.vc_count}</strong></div>
        </div>
      </div>
      <div class="sample-card">
        <div class="sample-head">
          ${playButton(payload.sample.audio, "Source Audio")}
          <div>
            <div class="sample-title">Source Audio</div>
            <div class="sample-meta">${escapeHtml(sampleMeta)}</div>
          </div>
        </div>
        <p class="sample-note">${escapeHtml(payload.sample.note || payload.meta.sample_note || "")}</p>
        ${transcript}
      </div>
    </section>
  `;
}

function renderInfo(payload) {
  const steps = (payload.meta.reading_steps || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  const variants = (payload.meta.variant_guide || [])
    .map(renderLegendItem)
    .join("");

  return `
    <section class="info-grid">
      <article class="info-card">
        <div class="eyebrow">How To Read</div>
        <p class="info-copy">${escapeHtml(payload.meta.overview || "")}</p>
        <ul class="point-list">${steps}</ul>
      </article>
      <article class="info-card">
        <div class="eyebrow">Variant Guide</div>
        <div class="legend-list">${variants}</div>
      </article>
    </section>
  `;
}

function renderSummary(summary) {
  if (!summary || !Array.isArray(summary.rows) || !summary.rows.length) {
    return "";
  }

  const headers = summary.columns.map((col) => `<th>${escapeHtml(col.label)}</th>`).join("");
  const rows = summary.rows.map((row) => {
    const cells = summary.columns.map((col) => {
      const value = row[col.key];
      return `<td>${escapeHtml(value ?? "")}</td>`;
    }).join("");
    return `<tr>${cells}</tr>`;
  }).join("");

  return `
    <section class="summary-panel">
      <div class="summary-head">
        <div>
          <div class="eyebrow">Metrics Snapshot</div>
          <h2 class="summary-title">${escapeHtml(summary.title || "Results Table")}</h2>
        </div>
        <div class="summary-meta">
          <div class="stat-chip"><span>Source</span><strong>${escapeHtml(summary.source || "")}</strong></div>
          <div class="stat-chip"><span>Rows</span><strong>${escapeHtml(summary.row_count ?? "")}</strong></div>
          <div class="stat-chip"><span>Methods</span><strong>${escapeHtml(summary.method_count ?? "")}</strong></div>
        </div>
      </div>
      <p class="summary-note">${escapeHtml(summary.note || "")}</p>
      <div class="summary-scroll">
        <table class="summary-table">
          <thead>
            <tr>${headers}</tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderTree(payload) {
  return `
    <section class="tree-panel">
      <div class="stage-head">
        <span>Source / Defense</span>
        <span>Variants / Model Outputs</span>
      </div>
      <div class="pipeline-root">
        <div class="pipeline-tree" id="pipeline-tree">
          <svg class="tree-svg" id="tree-svg" aria-hidden="true"></svg>
          <div class="pipeline-grid">
            <div class="source-column">
              <div class="source-card" data-connect-id="source-root">
                <div class="source-head">
                  ${playButton(payload.sample.audio, "Source Audio")}
                  <div>
                    <div class="source-title">Original Audio</div>
                    <div class="source-note">${escapeHtml(payload.meta.sample_note || "")}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="branch-list">
              ${payload.branches.map((branch, index) => renderBranch(branch, index)).join("")}
            </div>
          </div>
        </div>
      </div>
    </section>
  `;
}

function buildMarkup(payload, summary) {
  return `
    ${renderHero(payload)}
    ${renderInfo(payload)}
    ${renderSummary(summary)}
    ${renderTree(payload)}
  `;
}

function pauseCurrent() {
  if (state.activeAudio) {
    state.activeAudio.pause();
    state.activeAudio.currentTime = 0;
  }
  if (state.activeButton) {
    state.activeButton.classList.remove("playing");
    state.activeButton.textContent = "▶";
  }
  state.activeAudio = null;
  state.activeButton = null;
}

function bindPlayback(root) {
  const buttons = [...root.querySelectorAll(".play-orb")];
  buttons.forEach((button) => {
    const src = button.dataset.audioSrc;
    if (!src) {
      button.disabled = true;
      return;
    }

    const audio = new Audio(src);
    audio.preload = "none";
    audio.addEventListener("ended", () => {
      if (state.activeAudio === audio) {
        pauseCurrent();
      }
    });

    button.addEventListener("click", (event) => {
      event.stopPropagation();
      if (state.activeAudio === audio) {
        pauseCurrent();
        return;
      }

      pauseCurrent();
      state.activeAudio = audio;
      state.activeButton = button;
      button.classList.add("playing");
      button.textContent = "❚❚";
      audio.play().catch(() => {
        pauseCurrent();
      });
    });
  });
}

function setActiveBranch(root, branchIndex) {
  state.activeBranch = branchIndex;
  if (branchIndex === null) {
    state.activeVariant = null;
  }

  root.querySelectorAll(".branch-row").forEach((row) => {
    const isActive = branchIndex !== null && row.dataset.branchIndex === String(branchIndex);
    row.classList.toggle("is-active", isActive);
    row.classList.toggle("is-inactive", branchIndex !== null && !isActive);
  });

  root.querySelectorAll(".tree-path").forEach((path) => {
    const shared = path.dataset.branchIndex === "shared";
    const sameBranch = branchIndex !== null && path.dataset.branchIndex === String(branchIndex);
    path.classList.toggle("is-active", branchIndex !== null && (shared || sameBranch));
    path.classList.toggle("is-inactive", branchIndex !== null && !(shared || sameBranch));
  });
}

function setActiveVariant(root, variantId) {
  state.activeVariant = variantId;
  root.querySelectorAll(".variant-pill-wrap").forEach((wrap) => {
    wrap.classList.toggle("is-active", wrap.dataset.variantId === variantId);
  });
}

function bindFocus(root) {
  const branchList = root.querySelector(".branch-list");

  root.querySelectorAll(".branch-row").forEach((row) => {
    const branchIndex = Number(row.dataset.branchIndex);

    row.addEventListener("mouseenter", () => {
      setActiveBranch(root, branchIndex);
    });

    row.addEventListener("click", (event) => {
      if (event.target.closest(".play-orb")) return;
      setActiveBranch(root, branchIndex);
    });

    row.querySelectorAll(".variant-pill-wrap").forEach((wrap) => {
      wrap.addEventListener("mouseenter", () => {
        setActiveBranch(root, branchIndex);
        setActiveVariant(root, wrap.dataset.variantId);
      });

      wrap.addEventListener("click", (event) => {
        if (event.target.closest(".play-orb")) return;
        setActiveBranch(root, branchIndex);
        setActiveVariant(root, wrap.dataset.variantId);
      });
    });
  });

  branchList?.addEventListener("mouseleave", () => {
    setActiveBranch(root, null);
  });
}

function drawTreeLines(root) {
  const tree = root.querySelector("#pipeline-tree");
  const svg = root.querySelector("#tree-svg");
  const source = root.querySelector('[data-connect-id="source-root"]');
  const defenses = [...root.querySelectorAll('[data-connect-id^="defense-"]')];
  if (!tree || !svg || !source || !defenses.length) return;

  const treeRect = tree.getBoundingClientRect();
  const sourceRect = source.getBoundingClientRect();
  const sourceX = sourceRect.right - treeRect.left;
  const sourceY = sourceRect.top + sourceRect.height / 2 - treeRect.top;
  const defenseLeftX = Math.min(...defenses.map((node) => node.getBoundingClientRect().left - treeRect.left));
  const trunkX = defenseLeftX - 22;
  const defenseCenters = defenses.map((node) => {
    const rect = node.getBoundingClientRect();
    return {
      xLeft: rect.left - treeRect.left,
      xRight: rect.right - treeRect.left,
      y: rect.top + rect.height / 2 - treeRect.top,
    };
  });
  const minY = Math.min(...defenseCenters.map((item) => item.y));
  const maxY = Math.max(...defenseCenters.map((item) => item.y));

  svg.setAttribute("width", String(tree.clientWidth));
  svg.setAttribute("height", String(tree.clientHeight));
  svg.setAttribute("viewBox", `0 0 ${tree.clientWidth} ${tree.clientHeight}`);

  const paths = [
    `<path class="tree-path trunk" data-branch-index="shared" d="M ${sourceX} ${sourceY} L ${trunkX} ${sourceY}" />`,
    `<path class="tree-path trunk" data-branch-index="shared" d="M ${trunkX} ${minY} L ${trunkX} ${maxY}" />`,
  ];

  defenseCenters.forEach((defense, index) => {
    paths.push(`<path class="tree-path branch" data-branch-index="${index}" d="M ${trunkX} ${defense.y} L ${defense.xLeft} ${defense.y}" />`);
    const pills = [...root.querySelectorAll(`.branch-row[data-branch-index="${index}"] .variant-pill-wrap`)];
    pills.forEach((pill) => {
      const rect = pill.getBoundingClientRect();
      const xLeft = rect.left - treeRect.left;
      const y = rect.top + rect.height / 2 - treeRect.top;
      paths.push(`<path class="tree-path branch" data-branch-index="${index}" d="M ${defense.xRight} ${defense.y} L ${xLeft} ${y}" />`);
    });
  });

  svg.innerHTML = paths.join("");
}

function renderPipeline(payload, summary) {
  pauseCurrent();
  state.activeBranch = null;
  state.activeVariant = null;
  state.pipeline = payload;
  els.root.innerHTML = buildMarkup(payload, summary);
  bindPlayback(els.root);
  drawTreeLines(els.root);
  bindFocus(els.root);
}

async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadPipeline() {
  const [payload, summary] = await Promise.all([
    fetchJSON(PIPELINE_URL),
    fetchJSON(SUMMARY_URL).catch(() => null),
  ]);
  renderPipeline(payload, summary);
}

window.addEventListener("resize", () => {
  if (els.root.querySelector("#pipeline-tree")) {
    drawTreeLines(els.root);
  }
});

loadPipeline().catch((error) => {
  els.root.innerHTML = `<div class="error">Failed to load pipeline: ${escapeHtml(error.message)}</div>`;
});
