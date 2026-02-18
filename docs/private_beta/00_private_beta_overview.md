# Private Beta Overview

## What HDIS is
HDIS is a structured uncertainty-analysis system for a single candidate against a single job context. It captures hypotheses, risks, assumptions, and interview guidance as constrained artifacts.

## What HDIS is not
HDIS is not an ATS, not a screening engine, not a ranking system, and not a hiring decision system of record. It does not produce shortlist/reject/hire outcomes.

## What this beta is testing
- System stability under real recruiter workflows.
- Tenant isolation and leakage resistance.
- Validator and drift resistance against forbidden language and summary pressure.

This beta is not testing hiring outcomes.

## Success criteria for private beta
- 30 consecutive days with 3-5 recruiting firms.
- No verified cross-tenant leakage.
- No persisted drift into ranking, verdict, or summary language.
- Safety gates and go/no-go checks remain passing.

## Required references
- Operational checklist: `backend/PRIVATE_BETA_30_DAY_CHECKLIST.md`
- Go/no-go runner: `backend/scripts/run_go_no_go.py`
- Incident process: `docs/private_beta/05_incident_reporting_and_logs.md`
