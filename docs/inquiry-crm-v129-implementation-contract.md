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
| 備考 | InquiryID, product, maker, same-origin source path only | Strip query/hash/unknown hosts; never copy private URL tokens |
| SourceID | inquiry_id | Unique event idempotency/ref |
| ImportBatchID | existing import writer | Empty |

This is a **proposed row**, not a committed entry. The existing inbound writer must perform a prior SourceID lookup under a verified lock before any actual write; never implement blind append/replay.

## University Person Identity / Evidence Gate

1. Read customer candidates from the existing 02_顧客Master under a verified read-only snapshot.
2. Exact matching normalized email can suggest an existing record, but must also match verified name, affiliation and canonical CustomerID.
3. Multiple email hits, renamed affiliation, conflicting name, unverified Primary status/source, or stale/non-verified snapshot => HOLD.
4. New public-form email is **self-declared**, not university-verified: route to existing `00_新規受付` and hold pending evidence. Never auto-enable T055 marketing or overwrite the existing Primary email.
   - Live read-only physical `02_顧客Master` Q-column `メール状態` values include `確認済`, `確認済み`, `有効`, `要再調査`, `未確認`. `有効` by itself is **not** G02 evidence or verified Person identity; require the existing T006 Evidence and Dedup Gate to pass explicitly, plus an official source URL.
5. No PAI/ERP reverse write into Person name/affiliation/Primary.
6. A client-supplied CustomerID is never trusted; only the official Master candidate can provide a CustomerID.

## Existing 02_顧客Master physical 71-column projection (read-only)

The adapter `crmV129PersonFromMasterPhysicalRow_(headers, row, trustedT006Gates)` validates unique Japanese column headers and returns a read-only Person snapshot. Observed columns (zero-based physical positions): `顧客ID` A/0, `大学・所属` D/3, `研究者名` F/5, `Primaryメール` O/14, `メール状態` Q/16, `メール情報源URL` R/17, `氏名一致` AC/28, `所属一致` AD/29, `営業利用可否` AH/33, `ID状態` BO/66, `メール重複` BQ/68.

Physical `メール状態` includes `確認済`, `確認済み`, `有効`, `要再調査`, `未確認`. Even when `確認済` appears, **trusted T006 official-email-evidence and identity/dedup approvals are independent mandatory flags**. `有効` alone is not Person verification. The PAI/ERP reverse writer must not change these identity columns. The adapter reads no live data itself and performs no API requests.

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


## Continuation of 「剩余工作调查」 — 2026-11-03 JST

The existing V128/V129 design, T006 identity ownership, 27-to-17 column mapping, corporate HOLD route, explicit Case event gate, separate notification evidence, and CEO exact-SHA release boundary remain unchanged. Continue existing Draft PR #127 and Issue #166; do not create another CRM, Master, GAS project, Runner or Automation. Product Page V3.1 and official-media work remain separate; this increment changes no product page, CTA, `Code.gs`, workflow or production setting. PR #163 marketing attribution is a separate unfinished workstream, not implicitly released here.

### CRM-V129-DATE-20261103-01 — receipt-date projection defect

Reproduced at baseline `9f30f5c2db783a595caeebaf2a1be367cfcd1774`: serialized `2026-11-03T16:30:00Z` incorrectly projected to `2026-11-03` instead of JST `2026-11-04`; invalid `2026-02-30` and `2026-11-03junk` were accepted by the prefix-only date parser. `evaluateCrmHandoffV129_` did not reject an invalid receipt timestamp before preparing an intake/case candidate.

The pure date projection now converts true Date objects and explicit UTC/offset timestamps to JST. Existing timezone-free `yyyy-MM-dd` and `yyyy-MM-dd HH:mm:ss[.SSS]` Sheet values retain their existing JST meaning. Full-string/calendar validation rejects impossible dates, trailing content, invalid times/offsets, non-date types and out-of-range Date objects. Invalid receipt time produces `INVALID_INQUIRY`, no proposed intake and no CaseEvent candidate; no record is changed or discarded in the existing source ledger.

Permanent regression cases S25–S30 cover equivalent timestamps, JST midnight/year/leap-day boundaries, invalid input, extreme/spoofed Date values and Case gate fail-closed behavior. Run the existing suite:

```text
node --test tests/inquiry-dev-contract.test.cjs tests/identity-dedup-contract.test.cjs tests/inquiry-to-crm-v129-contract.test.cjs
```

AA8-N-012 isolated result: **52 total / 50 PASS / 0 FAIL / 2 TODO**. The two real email / CRM integration evidence tasks remain TODO; this is not live DEV or Production acceptance. Independent exact-commit QA and GitHub CI must be recorded on PR #127 after verification.

### Deployment evidence boundary

Existing DEV Sheet metadata and the historical Drive `inquiry-api/Code.gs` source file do not establish an active DEV deployment. This continuation's bounded search of AA8-N-018 Documents found no reference to the DEV Sheet ID; that is not proof that the deployment does not exist. Script ID, deployment/version, bound DEV Sheet and internal-only recipients must still be proven as one consistent existing deployment before any real POST. No replacement environment or Production test is authorized.


### 2026-11-04 | Corporate PAI route and QA CustomerID collision hardening

Read-only production sources confirm two real external corporate Inquiry records.
Unicast's original InquiryID is already recorded under existing PAI SalesCaseID
017; Midori is not found in the inspected PAI case range. No matching enterprise
organizations or domains are in the university Person Master.
Do not duplicate the Unicast case, create a fabricated corporate CustomerID, or
write a corporate visitor into the university Person Master.

V129 previously assigned HOLD_CUSTOMER_ID to a corporate quote/PoC event,
which could be misinterpreted as requiring a university L-xxxx Person ID.
PAI ERP v2.6 instead accepts InboundIntakeRef before SalesCaseID, without
a university Person ID. Corporate strong events now retain the deterministic
candidate CaseEventID but remain HOLD_PAI_CORPORATE_EVIDENCE_AND_WRITER.
The PAI organization writer is unverified; no Case is created and all
writesPerformed/emailsSent remain zero. Unknown entity strong events are
HOLD_ENTITY_CLASSIFICATION, not university ID allocation.

The isolated QA workbook contains noncanonical L-0001/L-0002 test strings
which also exist independently in the official Person Master. Their raw string
equality is NOT authority, and no QA ID may be imported, linked or promoted to
a production ID. The existing T006 admission gate rejects preset Intake IDs,
even when supplied alongside apparently valid Evidence.

New deterministic regressions use synthetic emails and no production records,
test the corporate/ambiguous strong-event boundary and QA ID collision, and
must not be presented as a real corporate PAI writer integration. Actual
Production CRM/Case E2E remains blocked until the authorized PAI writer and
formal identity evidence are verified in a separate approved change set.
