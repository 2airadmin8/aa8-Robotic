# Factory Efficiency｜SSOT Metric Contract

Repository ledger: ops/hp-factory-efficiency.csv.
Validator: scripts/hp_factory_efficiency.py.
Report: ops/hp-factory-efficiency-report.json.

Data definitions:
- source_ready_at = confirmed complete official manufacturer facts and approved media, not issue-created timestamp.
- preview_ready_at = real reachable exact SHA HTML Preview for CEO/product review.
- first_qa_at = first independent test evidence for exact candidate.
- manual_code_edits = human-requested manual source modifications, not AI commits.
- rework_iterations = bounded AI patch/QA loops, 0..3; failures are not silently retried.
- ceo_interventions = genuine CEO approvals/rejections, not bot comments.
- repeated_bug_count = real repeated root causes after a previous closure.
- evidence_url = authentic same-repository GitHub PR/issue.
- record_status = VERIFIED only when provenance and both time boundaries exist; else HISTORICAL_INCOMPLETE.

Bootstrap: H2 Plus and A3 Ultra have actual release/QA evidence but no trustworthy source-ready→first Preview timestamps. Do not fill guesses, report 0 comparable and no claimed cycle-time improvement.

Goal: 1 day from eligible source ready to Preview for routine models, but goal is not a present fact. Compare >=2 equivalent verified SKUs, plus first pass QA, repeated defects and CEO interventions. Protect data: no customer personal data or CRM details in ledger.
