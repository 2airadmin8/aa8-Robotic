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

## PM/CTO efficiency / automation maturity stop rules
- L1: two opted-in configured Factory products out of the 13-site catalog; not four-family mass production proof.
- L2: PR #175 generalized CEO rejection path is merged in main, **real reject-to-new-Preview E2E NOT_EXERCISED**. A synthetic test is not proof of autonomous production.
- L3: existing weekly GSC+Inquiry read-only reports propose up to 3 hypotheses; multiple weeks of actual business outcomes NOT YET PROVEN. No new task, scheduler, data master or CRM production writes.
- Efficiency ledger: historical H2 Plus/A3 Ultra records remain incomplete; 0 comparable cycles. Record exact source-ready, first reachable Preview, first independent QA, number of manual edits, AI iterations, CEO interventions and repeat defects on the next real SKU.
- Product performance target (e.g. 1 business day to Preview) is a TARGET, not historical fact. No invented percentage reduction.
- Stop optional polishing once approved product baseline and all mandatory gates pass. Any incremental changes require objective measured customer/ROI hypothesis and explicit bounded scope.
