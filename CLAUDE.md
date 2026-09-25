# Sentinel — Project Rules (Claude Code)

This file is authoritative. It hardcodes decisions already made. Do not
re-derive, re-negotiate, or "improve" these unless Caroline explicitly
changes one in a session and asks you to update this file. If a task
conflicts with a rule below, stop and flag the conflict rather than
picking one side.

This file is not legal advice, and nothing Sentinel produces is legal
advice. See "Legal and regulatory guardrails" below — those items require
a solicitor, not an AI coding session, before they're closed out.

## Who Caroline is (public-facing framing only)

- Professional title: **Financial Crime Analyst/Investigator**. Never
  "legal professional," never "lawyer."
- Credentials referenced publicly: **LLB only.** Never reference a PGCert,
  LLM, or any qualification beyond the LLB in anything Sentinel-facing
  (bios, UI copy, reports, exports, commit messages that might be public,
  READMEs). Never post or reproduce the PGCert certificate itself,
  anywhere, in any form.
- If any code, doc, or generated content surfaces a credential beyond
  "LLB," treat that as a bug and fix it before continuing.

## What Sentinel currently is

Three components, at different levels of reality. Do not conflate them
or imply one is more finished than it is:

1. **Transaction-monitor** (`transaction-monitor/`) — real, working
   FastAPI/SQLAlchemy backend. Four deterministic rules (large
   transaction, daily volume, frequency, unusual hours). No AI, no
   hallucination risk in this component; risk here is security and data
   handling, not truthfulness.
2. **Screening/KYC/EDD/SAR UI** — a single-file HTML mockup. Hardcoded
   fake entities, randomly generated match scores, no real sanctions
   list data, no backend. This is a design reference, not a working
   product. Never present it as functional.
3. **Claims register / Research & Verification** — the newest component.
   Publishes factual, statistical claims about financial crime and
   AML/CFT regulatory effectiveness, sourced from primary data. This is
   where the strictest rules apply (below), because its whole value
   proposition is being more rigorous than the institutions it checks.

## Who uses Sentinel, and when

- **Now, through Stages 1–3: Caroline only.** No third-party data, no
  external users.
- **Stage 4 target: institutional** — fintechs and financial
  institutions as users. Do not build features that assume real
  third-party customer data is already flowing before Stage 4 is
  explicitly reached and its legal prerequisites (see below) are closed.

## Production stages (gate sequentially — do not skip ahead)

1. Security hardening of the transaction-monitor (in progress — see
   Security section below for current state).
2. Claims register pilot: prove the discipline against 2–3 real issues
   before building tooling around it.
3. Encode the verification methodology as a reusable skill once proven.
4. Transaction-monitor real deployment — **blocked** until Stage 1 is
   complete AND a real user/data scenario is legally scoped (data
   processor/controller status, DPA if needed).
5. Correlation engine as a proper module (new FastAPI router, own data
   model) once the claims register dataset justifies automating it.
6. Public website — only once verified content exists to host.

## Security state (transaction-monitor)

Fixed, 2026-09-23/25 (local commit `c930429`, needs pushing from a
real authenticated environment):
- `python-multipart` upgraded to `>=0.0.22` (was 0.0.17 — CVE-2024-53981,
  CVE-2026-24486).
- `fastapi` upgraded to `>=0.129.0`, `starlette` pinned `>=1.3.1`, to
  clear transitive Starlette CVEs (CVE-2025-54121, CVE-2025-62727,
  CVE-2026-48710 "BadHost").
- Weekly `pip-audit` CI added at
  `.github/workflows/dependency-audit.yml`. Keep this green. A failing
  audit blocks any further work on this component until resolved.

Still outstanding, required before Stage 4 (real deployment):
- No authentication on any endpoint, including `DELETE /api/data` which
  currently wipes all data with zero protection. This is the top
  priority once Stage 4 work starts.
- SQLite → PostgreSQL migration.
- TLS termination (reverse proxy).
- Rate limiting.
- CSV upload size cap; strict `transaction_type` validation (currently
  silently defaults unrecognised values to "payment" — this is a
  correctness bug, not just a security one, fix it regardless of stage).
- Log rotation and access restriction on `transaction_monitor.log`
  (currently unrotated plaintext, contains real account IDs and amounts
  once real data flows).

## Claims register rules — hard constraints, not preferences

These govern any code, prompt, or document that produces or assists
with claims-register content. They are not stylistic suggestions.

1. **Never fabricate or estimate a figure to fill a gap.** If a primary
   source can't be found or verified, the claim's status is "Pending
   verification," not a guessed number. This includes MoJ prosecution
   data, SARs figures, or anything else — pull the real figure or leave
   it blank and say so.
2. **Only two output types exist:**
   - **Statistical Correlation** — computed directly from primary data
     (r-value, n, period, confounders). Never worded as causation. No
     "drives," "causes," "leads to."
   - **Attributed Causation** — a causal claim already made by a named,
     credible source, relayed with attribution. Sentinel never
     originates a causal conclusion of its own.
3. **Source-quality tiers**, required on every claim:
   - Independent (academic review, parliamentary committee, inspectorate)
   - Self-assessed (a regulator's claim about its own measures — flag
     this explicitly every time it's used, e.g. "claim made by the body
     whose own performance it describes")
   - Journalism (Bloomberg, FT, trade press — lowest weight, attributable
     but never presented with the authority of a primary source)
4. **Citations: OSCOLA format, most recent edition, every time.**
   No exceptions for internal/draft content either — build the habit
   into the tooling, not just the published output.
5. **Never pull figures from Bloomberg or other paywalled/licensed
   sources directly.** Cite and link to journalism as commentary; pull
   the underlying number from the primary regulator or institute the
   article is reporting on.
6. **Every claims register row needs:** claim, type, primary source,
   source tier, metric(s), period, computed result, confounders/caveats,
   status, issue reference. A row missing any of these is not
   "Verified," regardless of how good the number looks.
7. **Validate before marking "Verified."** Run the equivalent of a
   data-validation pass (sample size, confounders, methodology check)
   before a row's status changes. Don't just compute a correlation and
   call it done.

## Defamation guardrail — the single highest legal-risk item in this project

Never name a real entity or individual in connection with financial
crime, money laundering, or sanctions evasion unless the claim rests on
a **final adjudicated finding** (conviction, tribunal decision, upheld
regulatory finding). An allegation, an ongoing investigation, or a
journalist's characterization is not sufficient grounds to publish a
named claim. If a task would involve drafting content that names a real
party in this context, flag it for legal review before drafting rather
than after.

## Legal-advice disclaimer — fixed placement

Every claims register export/report, and the public bio wherever
Sentinel is introduced, must carry a visible statement that Sentinel's
output is factual/statistical analysis and does not constitute legal
advice. This is not optional boilerplate — treat its absence as a
publishing blocker.

## Legal and regulatory guardrails (need a solicitor, not a coding session)

Do not treat any of the following as resolved by writing code. These
are open legal questions:

- **Data controller/processor status** — undetermined. Must be resolved
  before any third-party data (Stage 4).
- **MLR 2017** — Sentinel as a software provider is not itself an
  "obliged entity" by default (obliged entities are defined categories:
  credit/financial institutions, auditors, legal professionals, estate
  agents, etc.). If Sentinel is ever used by an obliged entity for their
  own compliance, that entity retains its own statutory obligations —
  Sentinel supports, never replaces, their compliance function.
- **UK GDPR / DUAA 2025** — automated decision-making rules changed
  (old Article 22 → new Articles 22A–22D, conditions-based). The ICO's
  statutory AI/ADM Code of Practice was expected summer 2026 — confirm
  current publication status before relying on any assumption about it.
- **EU AI Act** — only relevant if Sentinel's output reaches the EU
  market or meaningfully affects EU residents. High-risk deadline
  (Annex III) status was unresolved as of the last check (originally
  2 Aug 2026, a delay to Dec 2027 was agreed in principle but pending
  formal adoption) — confirm current status before any EU-facing
  deployment.
- **FCA** — no AI-specific rules currently planned; supervised through
  existing frameworks (Consumer Duty, SM&CR).

## Out of scope / deferred (do not build without explicit instruction)

- User-submitted datasets or public interactivity in the claims register
  ("let users input their own data") — deliberately deferred. Building
  this triggers Online Safety Act / Ofcom considerations that haven't
  been scoped.
- A public website for Sentinel — deferred until verified content exists
  to host.
- The screening/KYC/EDD/SAR module becoming real (sanctions list
  ingestion, fuzzy matching) — not currently scheduled; a separate,
  larger effort than anything else in this project.

## Current handover task

Pull real Ministry of Justice prosecution/conviction figures for money
laundering (principal offence, England & Wales) from the Criminal
Justice Statistics Quarterly "Outcomes by Offence" data tool
(gov.uk / data.justice.gov.uk), matched to these already-verified SARs
figures, so the SARs-vs-Prosecutions claims register row can be
completed honestly:

| Year | SARs received (NCA UKFIU) |
| --- | --- |
| 2021–22 | 901,255 |
| 2022–23 | 859,000 |
| 2023–24 | 872,048 |

Source: National Crime Agency, *SARs Annual Report 2024* (NCA 2024);
as reported in Macfarlanes LLP, 'Suspicious Activity Reports: signs of
quality over quantity?' (3 April 2024)
<https://www.macfarlanes.com/insights/102j4d8/> accessed 25 September
2026.

One verified single-year data point exists for sentencing: 1,083
sentences for money laundering in the year ending June 2022 (Home
Office, *Economic Crime Plan 2 2023–2026 — Data Annex*). This is not a
series — do not treat it as one.

Working file: `claims-register/sars-vs-prosecutions.md` — continue this,
don't start a new one.

Once the prosecution series is pulled: compute the correlation, apply
the causation/correlation rule above, cite in OSCOLA, run a validation
pass, and only then move the row's status to "Verified."
