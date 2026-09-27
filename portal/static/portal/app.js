const COVER = ["life", "health", "motor", "property", "travel"];
const DOC_TYPES = ["policy", "claim", "underwriting", "identity", "other"];
const ID_TYPES = ["passport", "drivers_license", "national_id"];
const CASH_TYPES = ["payment", "refund", "premium", "claim_payout", "adjustment"];
const STATUS = {
  underwriting: ["submitted", "in_review", "referred", "approved", "declined"],
  policies: ["draft", "quoted", "active", "lapsed", "cancelled", "expired"],
  claims: ["intake", "under_review", "approved", "rejected", "settled"],
  invoices: ["draft", "issued", "overdue", "paid", "void"],
  rules: ["active", "inactive"],
};

const TITLES = {
  overview: "Overview",
  customers: "Customers",
  underwriting: "Underwriting",
  policies: "Policies",
  claims: "Claims",
  finance: "Finance",
  compliance: "Compliance",
  documents: "Documents",
  identity: "Identity",
};

let token = sessionStorage.getItem("bfsi_token") || "";
let me = null;

const $ = (selector) => document.querySelector(selector);

function errorText(data) {
  if (!data) return "Request failed.";
  if (typeof data.detail === "string") return data.detail;
  return Object.entries(data)
    .map(([key, value]) => `${key}: ${[].concat(value).join(" ")}`)
    .join(" ");
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...options, headers });
  const text = await response.text();
  let data = null;
  if (text) data = JSON.parse(text);
  if (!response.ok) throw new Error(errorText(data));
  return data;
}

function toast(message) {
  const node = $("#toast");
  node.hidden = !message;
  node.textContent = message || "";
}

function showLogin(message) {
  $("#app").hidden = true;
  $("#login-screen").hidden = false;
  const error = $("#login-error");
  error.hidden = !message;
  error.textContent = message || "";
}

function showApp() {
  $("#login-screen").hidden = true;
  $("#app").hidden = false;
  $("#who").textContent = `${me.username} · ${me.role.replaceAll("_", " ")}`;
}

function results(data) {
  return data.results || data;
}

function cell(text) {
  const node = document.createElement("td");
  node.textContent = text ?? "—";
  return node;
}

function emptyRow(body, columns, message) {
  body.replaceChildren();
  const row = document.createElement("tr");
  const node = document.createElement("td");
  node.colSpan = columns;
  node.className = "empty";
  node.textContent = message;
  row.append(node);
  body.append(row);
}

function statusSelect(url, current, choices) {
  const select = document.createElement("select");
  select.className = "status-select";
  choices.forEach((choice) => {
    const option = document.createElement("option");
    option.value = choice;
    option.textContent = choice.replaceAll("_", " ");
    option.selected = choice === current;
    select.append(option);
  });
  let selected = current;
  select.addEventListener("change", async () => {
    const next = select.value;
    try {
      await api(url, { method: "PATCH", body: JSON.stringify({ status: next }) });
      selected = next;
      toast("");
    } catch (error) {
      toast(error.message);
      select.value = selected;
    }
  });
  const wrap = document.createElement("td");
  wrap.append(select);
  return wrap;
}

function fillChoices(select, choices, placeholder) {
  select.replaceChildren();
  if (placeholder) {
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = placeholder;
    select.append(blank);
  }
  choices.forEach((choice) => {
    const option = document.createElement("option");
    option.value = choice.value ?? choice;
    option.textContent = choice.label ?? String(choice).replaceAll("_", " ");
    select.append(option);
  });
}

function customerOptions() {
  return results(window.__customers || { results: [] }).map((customer) => ({
    value: customer.id,
    label: customer.name,
  }));
}

function policyOptions(activeOnly) {
  return results(window.__policies || { results: [] })
    .filter((policy) => !activeOnly || policy.status === "active")
    .map((policy) => ({
      value: policy.id,
      label: `${policy.policy_number} · ${policy.customer_name}`,
    }));
}

function fillCustomerSelects() {
  document.querySelectorAll('select[name="customer"]').forEach((select) => {
    const current = select.value;
    fillChoices(select, customerOptions());
    if (current) select.value = current;
  });
}

async function loadList(path) {
  return api(`${path}${path.includes("?") ? "&" : "?"}page_size=100`);
}

async function loadOverview() {
  const [customers, policies, claims, underwriting] = await Promise.all([
    loadList("/api/customers/"),
    loadList("/api/policies/?status=active"),
    loadList("/api/claims/?fraud_flagged=true"),
    loadList("/api/underwriting/"),
  ]);
  const stats = [
    ["Customers", customers.count],
    ["Active policies", policies.count],
    ["Fraud flags", claims.count],
    ["Underwriting", underwriting.count],
  ];
  const statsNode = $("#stats");
  statsNode.replaceChildren();
  stats.forEach(([label, value]) => {
    const card = document.createElement("article");
    card.className = "stat";
    const strong = document.createElement("strong");
    strong.textContent = value;
    const span = document.createElement("span");
    span.textContent = label;
    card.append(strong, span);
    statsNode.append(card);
  });

  const balances = $("#balances");
  balances.replaceChildren();
  for (const customer of customers.results.slice(0, 4)) {
    const balance = await api(`/api/finance/customers/${customer.id}/outstanding-balance/`);
    const card = document.createElement("article");
    card.className = "balance";
    const strong = document.createElement("strong");
    strong.textContent = balance.outstanding_balance;
    const span = document.createElement("span");
    span.textContent = `${balance.customer_name} outstanding · invoices ${balance.open_invoice_total} − payments ${balance.payment_total} + refunds ${balance.refund_total}`;
    card.append(strong, span);
    balances.append(card);
  }
}

async function loadCustomers() {
  const data = await loadList("/api/customers/");
  window.__customers = data;
  fillCustomerSelects();
  const body = $("#customer-rows");
  if (!data.results.length) {
    emptyRow(body, 4, "No customers yet.");
    return;
  }
  body.replaceChildren();
  data.results.forEach((customer) => {
    const row = document.createElement("tr");
    row.append(cell(customer.name), cell(customer.email), cell(customer.phone), cell(customer.address));
    body.append(row);
  });
}

async function loadUnderwriting() {
  const data = await loadList("/api/underwriting/");
  const policyForm = $("#policy-form select[name='underwriting_request']");
  fillChoices(
    policyForm,
    data.results.filter((item) => item.status === "approved").map((item) => ({
      value: item.id,
      label: `#${item.id} ${item.customer_name} · ${item.policy_type}`,
    })),
    "None",
  );
  const body = $("#underwriting-rows");
  if (!data.results.length) {
    emptyRow(body, 4, "No underwriting requests yet.");
    return;
  }
  body.replaceChildren();
  data.results.forEach((item) => {
    const row = document.createElement("tr");
    row.append(
      cell(item.customer_name),
      cell(item.policy_type),
      cell(item.details),
      statusSelect(`/api/underwriting/${item.id}/`, item.status, STATUS.underwriting),
    );
    body.append(row);
  });
}

async function loadPolicies() {
  const [data, approved] = await Promise.all([
    loadList("/api/policies/"),
    loadList("/api/underwriting/?status=approved"),
  ]);
  window.__policies = data;
  fillChoices(
    $("#policy-form select[name='underwriting_request']"),
    approved.results.map((item) => ({
      value: item.id,
      label: `#${item.id} ${item.customer_name} · ${item.policy_type}`,
    })),
    "None",
  );
  document.querySelectorAll("select[name='policy']").forEach((select) => {
    const activeOnly = select.form && select.form.id === "claim-form";
    fillChoices(select, policyOptions(activeOnly), select.name === "policy" && !activeOnly ? "None" : null);
  });
  const body = $("#policy-rows");
  if (!data.results.length) {
    emptyRow(body, 6, "No policies yet.");
    return;
  }
  body.replaceChildren();
  data.results.forEach((policy) => {
    const row = document.createElement("tr");
    row.append(
      cell(policy.policy_number),
      cell(policy.customer_name),
      cell(policy.type),
      cell(policy.premium_amount),
      cell(`${policy.start_date} → ${policy.end_date}`),
      statusSelect(`/api/policies/${policy.id}/`, policy.status, STATUS.policies),
    );
    body.append(row);
  });
}

async function loadClaims() {
  const data = await loadList("/api/claims/");
  const body = $("#claim-rows");
  if (!data.results.length) {
    emptyRow(body, 6, "No claims yet.");
    return;
  }
  body.replaceChildren();
  data.results.forEach((claim) => {
    const row = document.createElement("tr");
    const flags = document.createElement("td");
    if (claim.fraud_flags && claim.fraud_flags.length) {
      const wrap = document.createElement("div");
      wrap.className = "chips";
      claim.fraud_flags.forEach((flag) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = flag.replaceAll("_", " ");
        wrap.append(chip);
      });
      flags.append(wrap);
    } else {
      flags.textContent = "Clear";
      flags.className = "ok";
    }
    row.append(
      cell(claim.claim_number),
      cell(claim.policy_number),
      cell(claim.claimant_name),
      cell(claim.amount),
      flags,
      statusSelect(`/api/claims/${claim.id}/`, claim.status, STATUS.claims),
    );
    body.append(row);
  });
}

async function loadFinance() {
  const data = await loadList("/api/finance/invoices/");
  const body = $("#invoice-rows");
  if (!data.results.length) {
    emptyRow(body, 5, "No invoices yet.");
    return;
  }
  body.replaceChildren();
  data.results.forEach((invoice) => {
    const row = document.createElement("tr");
    row.append(
      cell(invoice.invoice_number),
      cell(invoice.customer_name),
      cell(invoice.amount),
      cell(invoice.due_date),
      statusSelect(`/api/finance/invoices/${invoice.id}/`, invoice.status, STATUS.invoices),
    );
    body.append(row);
  });
}

async function loadCompliance() {
  const [rules, reports] = await Promise.all([
    loadList("/api/compliance/rules/"),
    loadList("/api/compliance/reports/"),
  ]);
  const ruleBody = $("#rule-rows");
  ruleBody.replaceChildren();
  if (!rules.results.length) emptyRow(ruleBody, 3, "No rules yet.");
  rules.results.forEach((rule) => {
    const row = document.createElement("tr");
    row.append(
      cell(rule.name),
      cell(rule.description),
      statusSelect(`/api/compliance/rules/${rule.id}/`, rule.status, STATUS.rules),
    );
    ruleBody.append(row);
  });
  const reportBody = $("#report-rows");
  if (!reports.results.length) {
    emptyRow(reportBody, 4, "No reports yet.");
    return;
  }
  reportBody.replaceChildren();
  reports.results.forEach((report) => {
    const row = document.createElement("tr");
    row.append(cell(report.report_number), cell(report.rule_name), cell(report.report_date), cell(report.status));
    reportBody.append(row);
  });
}

async function loadDocuments() {
  const data = await loadList("/api/documents/");
  const body = $("#document-rows");
  if (!data.results.length) {
    emptyRow(body, 4, "No documents yet.");
    return;
  }
  body.replaceChildren();
  data.results.forEach((item) => {
    const row = document.createElement("tr");
    const linkCell = document.createElement("td");
    if (item.url) {
      const link = document.createElement("a");
      link.href = item.url;
      link.textContent = "Open";
      linkCell.append(link);
    }
    row.append(cell(item.name), cell(item.type), cell(item.size), linkCell);
    body.append(row);
  });
}

async function loadIdentity() {
  const data = await loadList("/api/identity/verifications/");
  const body = $("#identity-rows");
  if (!data.results.length) {
    emptyRow(body, 5, "No identity checks yet.");
    return;
  }
  body.replaceChildren();
  data.results.forEach((item) => {
    const row = document.createElement("tr");
    row.append(
      cell(item.customer_name),
      cell(item.document_type),
      cell(item.document_number),
      cell(item.status),
      cell(item.result_detail),
    );
    body.append(row);
  });
}

const LOADERS = {
  overview: loadOverview,
  customers: loadCustomers,
  underwriting: loadUnderwriting,
  policies: loadPolicies,
  claims: async () => { await loadPolicies(); await loadClaims(); },
  finance: async () => { await loadCustomers(); await loadPolicies(); await loadFinance(); },
  compliance: loadCompliance,
  documents: loadDocuments,
  identity: loadIdentity,
};

async function openPanel(name) {
  document.querySelectorAll("aside button").forEach((button) => {
    button.classList.toggle("active", button.dataset.panel === name);
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.hidden = panel.id !== `panel-${name}`;
  });
  $("#panel-title").textContent = TITLES[name];
  toast("");
  try {
    if (name !== "customers") await loadCustomers();
    await LOADERS[name]();
  } catch (error) {
    toast(error.message);
  }
}

function formObject(form) {
  const payload = {};
  new FormData(form).forEach((value, key) => {
    if (value !== "") payload[key] = value;
  });
  return payload;
}

function bindForm(id, path, refresh) {
  $(id).addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await api(path, { method: "POST", body: JSON.stringify(formObject(event.target)) });
      event.target.reset();
      toast("");
      await refresh();
    } catch (error) {
      toast(error.message);
    }
  });
}

function prepareStaticSelects() {
  fillChoices($("#underwriting-form select[name='policy_type']"), COVER);
  fillChoices($("#policy-form select[name='type']"), COVER);
  fillChoices($("#payment-form select[name='type']"), CASH_TYPES);
  fillChoices($("#document-form select[name='type']"), DOC_TYPES);
  fillChoices($("#identity-form select[name='document_type']"), ID_TYPES);
  const today = new Date().toISOString().slice(0, 10);
  document.querySelectorAll("input[type='date']").forEach((input) => {
    if (!input.value) input.value = today;
  });
  const end = new Date();
  end.setDate(end.getDate() + 365);
  $("#policy-form [name='end_date']").value = end.toISOString().slice(0, 10);
}

async function enter() {
  me = await api("/api/auth/me/");
  showApp();
  prepareStaticSelects();
  await openPanel("overview");
}

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = formObject(event.target);
  try {
    const session = await api("/api/auth/login/", { method: "POST", body: JSON.stringify(payload) });
    token = session.access;
    sessionStorage.setItem("bfsi_token", token);
    await enter();
  } catch (error) {
    showLogin(error.message);
  }
});

document.querySelectorAll(".demo-row button").forEach((button) => {
  button.addEventListener("click", () => {
    $("#login-form [name='username']").value = button.dataset.user;
    $("#login-form [name='password']").value = button.dataset.pass;
    $("#login-form").requestSubmit();
  });
});

$("#logout").addEventListener("click", () => {
  token = "";
  sessionStorage.removeItem("bfsi_token");
  showLogin("");
});

document.querySelectorAll("aside button").forEach((button) => {
  button.addEventListener("click", () => openPanel(button.dataset.panel));
});

bindForm("#customer-form", "/api/customers/", loadCustomers);
bindForm("#underwriting-form", "/api/underwriting/", loadUnderwriting);
bindForm("#policy-form", "/api/policies/", loadPolicies);
bindForm("#claim-form", "/api/claims/", loadClaims);
bindForm("#invoice-form", "/api/finance/invoices/", loadFinance);
bindForm("#payment-form", "/api/finance/transactions/", loadFinance);
bindForm("#rule-form", "/api/compliance/rules/", loadCompliance);
bindForm("#identity-form", "/api/identity/verify/", loadIdentity);

$("#document-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(event.target);
  ["policy", "claim", "underwriting_request"].forEach((key) => {
    if (!data.get(key)) data.delete(key);
  });
  try {
    await api("/api/documents/", { method: "POST", body: data });
    event.target.reset();
    toast("");
    await loadDocuments();
  } catch (error) {
    toast(error.message);
  }
});

if (token) {
  enter().catch(() => showLogin("Sign in again."));
}
