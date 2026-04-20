# Undercurrent — Security and Privacy

**Concept anchor:** Reis & Housley 2022, ch. 10 ("Security and Privacy").
**Also drawing from:** NIST SP 800-53; GDPR Art. 32, Art. 17; OWASP Top 10 for APIs; Snowflake / BigQuery / Databricks access-control docs.

---

## Why it's an undercurrent

Security is not a stage — every stage generates, moves, stores, and serves data with access implications. Bolting on security at serving time is too late; sensitive data has already been copied through ingestion and transformation layers.

## The three CIA properties applied to data

- **Confidentiality** — only authorized principals can read.
- **Integrity** — data is not modified except through legitimate pipelines.
- **Availability** — authorized consumers can get the data when needed (SLAs overlap with DataOps).

## Principle of least privilege

Default deny. Access is granted per explicit need, per role, per dataset, per column when justified, per row when regulated.

Granularities, strongest to weakest:
1. **Cell-level / column masking** — specific columns (SSN, email) redacted for roles without clearance.
2. **Row-level security** — filter rows based on the querying principal's attributes (country, team).
3. **Column-level grants** — column subset visible per role.
4. **Table-level grants** — the standard unit in most warehouses.
5. **Schema / database grants** — coarsest; use for environments, not data sensitivity.

## PII identification and handling

Personal Identifiable Information — anything that alone or in combination can identify a person: names, emails, phone numbers, government IDs, device IDs, IP addresses, precise location, sensitive demographics.

Mandatory practices:
- **Tag PII in the catalog** at ingestion time. Never after. If you can't tag at ingestion, you can't enforce downstream.
- **Mask by default**, reveal on explicit grant.
- **Hash / tokenize** when identity is needed but literal value is not (e.g., join keys across systems).
- **Never log PII** — structured log pipelines must redact.

## Encryption

- **At rest** — enabled by default on cloud warehouses and object stores. Verify, don't assume.
- **In transit** — TLS 1.2+ for every client, every service-to-service hop, every replication stream.
- **Key management** — cloud KMS (AWS KMS, GCP KMS, Azure Key Vault). Customer-managed keys for regulated data.

## Compliance frames (brief)

- **GDPR** (EU) — lawful basis for processing, data subject rights (right to erasure, portability), breach notification 72h.
- **CCPA / CPRA** (California) — consumer rights to know / delete / opt out.
- **HIPAA** (US health) — PHI handling, BAAs with vendors.
- **SOC 2** (audit framework) — controls evidence for security, availability, confidentiality.
- **PCI DSS** (payments) — cardholder data environment isolation.

Data engineers are not lawyers. The responsibility is to make compliance technically possible: tagging, retention enforcement, deletion workflows, audit trails.

## Audit logging

Every access to sensitive data should be logged: who, what, when, from where. Cloud platforms provide this (AWS CloudTrail, GCP Audit Logs, Snowflake `ACCOUNT_USAGE`). Centralize logs in a SIEM or equivalent; retain per compliance requirements.

## Secrets management

- Never in code, never in env files committed to git.
- Use a secrets backend: AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, or orchestrator-native (Airflow Connections + Fernet, Dagster resources).
- Rotate on a schedule; automate rotation where possible.

## Anti-patterns

- Service account with broad wildcard permissions "because we were blocked."
- PII replicated to dev / staging without masking.
- Logs containing raw emails / IDs shipped to observability tools.
- Shared passwords for service accounts.
- "We'll tag PII later" — by then it's in twelve downstream tables.
- BI tools connected with an admin-level service account.

## See also

- Governance and cataloging (where PII tags live): `undercurrent-data-management.md`
- Cost of audit-log retention: `concept-finops.md`
