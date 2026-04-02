const summaryGrid = document.querySelector("#summary-grid");
const transitionList = document.querySelector("#transition-list");
const studyFamilyList = document.querySelector("#study-family-list");
const conditionTableBody = document.querySelector("#condition-table-body");

function makeCard(label, value, note) {
  const article = document.createElement("article");
  article.className = "card";
  article.innerHTML = `
    <p class="card-label">${label}</p>
    <div class="card-value">${value}</div>
    <div class="card-note">${note}</div>
  `;
  return article;
}

function makePill(text) {
  const span = document.createElement("span");
  span.className = "pill";
  span.textContent = text;
  return span;
}

function renderBadgeList(values) {
  if (!Array.isArray(values) || values.length === 0) {
    return "none";
  }

  return values
    .map((value) => `<span class="badge">${value}</span>`)
    .join("");
}

async function main() {
  const response = await fetch("./benchmark-snapshot.json");
  const data = await response.json();

  summaryGrid.append(
    makeCard("Bundle", data.bundle_id, `Generated ${new Date(data.generated_on).toLocaleString()}`),
    makeCard("Validation", data.validation.valid ? "valid" : "invalid", `${data.validation.condition_record_count} condition records checked`),
    makeCard("Fail Closed", data.shell.fail_closed ? "yes" : "no", `${data.outputs.controller_hazard_blocked_conditions.length} hazard-blocked conditions`),
    makeCard("Rule-Backed", String(data.coverage.rule_backed_condition_count), `${data.coverage.coverage_verdict}`),
    makeCard("Baseline Promote", String(data.outputs.baseline_output_counts.promote ?? 0), "age-only baseline"),
    makeCard("Controller Promote", String(data.outputs.controller_output_counts.promote ?? 0), "controller decision layer"),
  );

  Object.entries(data.outputs.transition_counts).forEach(([key, value]) => {
    transitionList.append(makePill(`${key}: ${value}`));
  });

  Object.entries(data.snapshot.study_family_counts).forEach(([key, value]) => {
    studyFamilyList.append(makePill(`${key}: ${value}`));
  });

  data.condition_records.forEach((record) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${record.condition_id}</td>
      <td>${record.study_family_id}</td>
      <td>${record.phase_layer}</td>
      <td>${record.primary_evidence_class}</td>
      <td>${renderBadgeList(record.active_negative_family_ids)}</td>
    `;
    conditionTableBody.append(row);
  });
}

main().catch((error) => {
  console.error(error);
  summaryGrid.append(
    makeCard("Demo Error", "failed", "Open the console for details."),
  );
});
