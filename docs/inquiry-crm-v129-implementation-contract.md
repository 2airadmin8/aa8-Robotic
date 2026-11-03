# AirAdmin8 Robotics｜Inquiry → Customer Master → PAI ERP（V129 DEV Contract）

- Approved requirement date: **2026-11-03 JST**
- Authoritative human-readable design: [Google Docs V129](https://docs.google.com/document/d/1aPtoen0Ev5y_fDssx4syRgPm2lH8_YtvNbDTyPlx4Qs/edit)
- Existing T006 Person SSOT and [PAI ERP v2.6](https://docs.google.com/document/d/1zOEcjFWhZesiaFXlqdyjWzLiJHkL97PiSV5QbxXLkrI/edit) retain ownership.
- This file is an **implementation contract**, not an independent Customer Master, not a second CRM, and not evidence of a live DEV/PROD Writer.
- Code: `ops/inquiry-api/CRM_Handoff_Contract.gs` (pure functions, no GAS side effects).
- Tests: `tests/inquiry-to-crm-v129-contract.test.cjs`, plus existing `inquiry-dev-contract.test.cjs` and `identity-dedup-contract.test.cjs`.

## Fixed business process

```text
Website product CTA + contact form
  -> existing doPost (response_token; submission_token idempotency)
  -> existing 01_Inquiry (27-col event ledger; INQ-* ID)
  -> V129 pure routing contract (NO WRITES)
     + UNIVERSITY => only 00_新規受付 (17 physical cols)
       -> existing Identity / Dedup / Evidence writer
       -> existing 02_顧客Master CustomerID
     + CORPORATE => existing PAI organization/account area (currently writer mapping BLOCKED)
     + UNKNOWN / CONFLICT => HOLD
  -> existing authorized Sales Owner / Follow-up Task
  -> explicit quote / meeting / PoC / purchase fact + CustomerID + CaseEventID
  -> existing PAI Writer creates SalesCaseID / CanonicalCaseID
  -> quotation -> proposal -> order -> delivery -> support
```

Inquiry ID != CustomerID != SalesCaseID != CanonicalCaseID != DeliverableID. Never infer them from one another. Page visits/open/PDF data do not create Cases.

## Verified physical field mapping (no schema mutation)

Source `01_Inquiry`: 27 columns. Canonical input fields from the existing form:
`inquiry_id`, `received_at`, `category`, `organization`, `name`, `email`, `phone`, `product`, `use_case`, `budget`, `schedule`, `development`, `message`, `source_page`, `source_product`, `source_maker`, `source_service`, `source_theme`, `source_case`, `utm_source`, `utm_medium`, `utm_campaign`, `ga_client_id`, `submission_token`, plus status/notification facts.

Destination **existing** `00_新規受付` physical 17 columns:

| Target physical header | Source | First draft state |
|---|---|---|
| 受付日 | received_at -> JST yyyy-MM-dd | Captured date |
| データ来源 | static `Robotics_Web_Inquiry` | Provenance label |
| 大学・所属 | organization | Self-declared, unverified |
| 研究室 | no field | Empty, never guess |
| 研究者名 | name | Self-declared, unverified |
| 役職 | no field | Empty |
| メール | email | Self-provided; NOT confirmed Primary |
| 電話 | phone | Self-provided |
| researchmap_URL | no source | Empty |
| KAKEN_URL | no source | Empty |
| 根拠URL | must be verified official evidence | **Empty**; source_page does not qualify |
| 重複確認 | existing Dedup Writer | `未確認` |
| 顧客ID | existing Person SSOT Writer | Empty until verified |
| 処理状態 | existing intake/identity writer | `HOLD_EVIDENCE` |
| 備考 | InquiryID, product, maker, source page | Truncated; no extra unrelated PII |
| SourceID | inquiry_id | Unique event idempotency/ref |
| ImportBatchID | existing import writer | Empty |

This is a **proposed row**, not a committed entry. The existing inbound writer must perform a prior SourceID lookup under a verified lock before any actual write; never implement blind append/replay.

## University Person Identity / Evidence Gate

1. Read customer candidates from the existing 02_顧客Master under a verified read-only snapshot.
2. Exact matching normalized email can suggest an existing record, but must also match verified name, affiliation and canonical CustomerID.
3. Multiple email hits, renamed affiliation, conflicting name, unverified Primary status/source, or stale/non-verified snapshot => HOLD.
4. New public-form email is **self-declared**, not university-verified: route to existing `00_新規受付` and hold pending evidence. Never auto-enable T055 marketing or overwrite the existing Primary email.
5. No PAI/ERP reverse write into Person name/affiliation/Primary.
6. A client-supplied CustomerID is never trusted; only the official Master candidate can provide a CustomerID.

## Corporate / Opportunity Gate

- `PAI_ORGANIZATION` is isolated from the university Person Master. The corporate Customer/Organization Writer's actual API and physical fields must be read and verified before enabling this route.
- Neither the Inquiry 27 columns nor intake 17 columns physically contain `CaseEventID`, `CanonicalCaseID`, `SalesCaseID`: they are **logical interface fields** owned by the PAI domain.
- Explicit `見積・大学購買` or `PoC設計` category can create only a deterministic **candidate** CaseEventID `InquiryID:QUOTE_REQUEST` or `InquiryID:POC_CONSULTATION`.
- Existing verified CustomerID, authorized Owner, event uniqueness and confirmed PAI Writer are all required before creating a real Case. General consultation, SDK and product comparison do not auto-create Cases.
- Notifications use existing systems; no new Gmail/Slack sender or trigger.

## DEV proof before any writer activation

Environment reality as of 2026-11-03: the CEO `clasp list` was accessible but exposed only a blank `myFunction` Apps Script project, **not** the Inquiry DEV deployment. Existing DEV spreadsheet is `1PzfHiB50jFDHCosMGTb7MUvbQ9nC3UD5pHjgHbpY9Qk`; the existence of this spreadsheet does NOT prove which Script currently binds it.

Blocking prerequisites:
- Inquiry DEV Script ID, Deployment ID/version, bound DEV Sheet ID and **internal-only test email recipient** all verified from the same actual deployment (no inference).
- DEV no-write preflight proves Production Sheet and recipient cannot be reached.
- DEV one true submission -> INQ ID -> 27 columns; second different submission -> distinct ID; same token -> one entry; modified payload same token -> explicit conflict.
- Intake SourceID unique, Person existing/new/conflict synthetic acceptance, corporate HOLD, PAI weak signals no Case, strong events only with CustomerID+CaseEventID.
- Separate real internal notification and customer acknowledgment delivery evidence **only with explicitly authorized internal test recipients**. Production outbound client mail=0.
- AA8-N-015 independent QA and CI after latest main synchronization; CEO separate approval of exact production change set; manual-only deployment once.

## Current code status

`CRM_Handoff_Contract.gs` is **pure** and returns `writesPerformed:0`, `emailsSent:0`, `universityIntake.committed:false` and an explicit gate status. It cannot create customers or cases without integration to the verified existing Writer. The prior Inquiry mock/Identity contracts remain; the two live E2E/real email/CRM tasks are deliberately not marked PASS.

**DO NOT** merge this Draft PR into Production or deploy GAS without explicit CEO authorization and all environment gates above. Do not create a second GAS/Sheet/CRM/Runner/Automation.
