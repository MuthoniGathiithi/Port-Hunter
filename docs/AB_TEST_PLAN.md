# A/B Test Plan & Software Test Plan  
**Project:** Facial Recognition Attendance System (Frontend + Backend)  
**Prepared:** 2026-02-13  
**Owner:** _TBD_  
**Version:** 1.0  
  
This document combines a standard software **Test Plan / Test Procedure** with an **A/B experiment plan** for evaluating changes to face recognition and liveness flows in production-like conditions.
  
---
  
## 1.0 Introduction
  
This document describes the test plan and test procedures for the Facial Recognition Attendance System:
  
- **Backend:** FastAPI API with Supabase (PostgreSQL), InsightFace (SCRFD + ArcFace), OpenCV/NumPy, JWT auth  
- **Frontend:** Vite + React UI for lecturer login, student registration (liveness), attendance capture, reports  
  
Testing covers functional correctness, model/threshold quality, performance, security, privacy, and real-user outcomes via an A/B test.
  
### 1.1 Goals and objectives
  
**Primary objectives**
  
- Prevent regressions in authentication, registration, unit management, and attendance session workflows.
- Validate face recognition quality (false accept/reject rates) and liveness robustness (spoof resistance).
- Ensure reliability (error rates), performance (latency), and operational readiness (logging, monitoring).
  
**A/B experiment objective**
  
- Quantitatively compare **Variant A (control)** vs **Variant B (treatment)** for the liveness/recognition pipeline and/or UI flow, using pre-defined success metrics and guardrails.
  
### 1.2 Statement of scope
  
**In scope (to be tested)**
  
- Backend API routes:
  - `app/routers/auth.py` (login/JWT flows)
  - `app/routers/units.py` (unit management)
  - `app/routers/registration.py` (student registration + liveness)
  - `app/routers/attendance.py` (sessions + recognition + reporting)
- Backend services:
  - `app/services/face_detection.py`
  - `app/services/face_normalization.py`
  - `app/services/face_recognition.py`
  - `app/services/matching.py` (thresholding / decision logic)
  - `app/services/liveness_detection.py`
- Security and data handling:
  - `app/utils/security.py` (password hashing, JWT helpers)
  - Input validation, file uploads, PII controls
- Frontend flows:
  - Lecturer authentication + session persistence
  - Student registration (camera capture + liveness)
  - Attendance capture (camera capture + recognition)
  - Attendance sessions management and reporting views
  
**Out of scope (not tested in this plan)**
  
- Non-functional requirements not measurable in the available environment (e.g., full campus network hardening).
- Hardware/OS driver issues on specific devices not represented in the test lab.
- Long-term model drift monitoring and re-training (covered by a separate ML Ops plan).
  
### 1.3 Major constraints
  
- **Privacy & compliance:** facial data is sensitive; test data handling must follow institutional policy (consent, retention, access control).
- **Dataset constraints:** availability of representative images/videos (lighting, pose, skin tones) affects fairness and quality results.
- **Hardware variability:** camera quality and client performance can dominate outcomes; results must be segmented by device class.
- **Compute:** face detection/embedding can be CPU intensive; performance tests must reflect expected deployment hardware.
- **External dependencies:** Supabase availability, network latency, and JWT secret/configuration impact integration tests.
  
---
  
## 2.0 Test Plan
  
### 2.1 Software (SCI’s) to be tested
  
**System under test (SUT)**
  
- `facial_recognition_backend/` FastAPI service (including SQL migrations under `migrations/`)
- `facial_recognition_frontend/` React client
  
**Explicit exclusions**
  
- Third-party libraries (InsightFace, OpenCV, Supabase SDK) are tested only via integration/behavioral coverage; their internal unit tests are not within scope.
  
### 2.2 Testing strategy
  
Testing is layered and risk-based:
  
- Unit tests focus on deterministic logic (security helpers, matching/threshold rules, image preprocessing utilities).
- Integration tests validate API routes end-to-end with a test database and stubbed model components where needed.
- Validation tests confirm that the system meets product requirements (functional acceptance + model quality targets).
- High-order tests cover performance, security, reliability, and an A/B experiment for real-user outcomes.
  
#### 2.2.1 Unit testing
  
**Targets**
  
- Backend: pure functions and decision logic (e.g., matching thresholds, JWT validation utilities, image decoding/validation).
- Frontend: utilities (API client), state store logic, and component-level behavior with mocked network/camera inputs.
  
**Selection criteria**
  
- Any module that implements custom rules, thresholds, input validation, or security-sensitive logic.
- Any bugfix/regression-prone areas (authentication, attendance submission, liveness pass/fail logic).
  
**Notes**
  
- Model inference should be mocked for unit tests unless deterministic fixtures are available.
  
#### 2.2.2 Integration testing
  
**Scope**
  
- API contract + route integration with database and auth:
  - create/update units
  - register student (including liveness gating and template/embedding storage)
  - create attendance session, submit captures, finalize reports
  
**Order**
  
1) Auth + authorization (JWT, roles)  
2) Units management  
3) Student registration  
4) Attendance sessions and recognition  
  
#### 2.2.3 Validation testing
  
Validation confirms the system is usable and meets acceptance criteria:
  
- End-to-end UI flows on supported browsers/devices.
- Model-quality validation on a curated test set:
  - face detection success rate under expected conditions
  - recognition accuracy at chosen threshold(s)
  - liveness robustness against common spoofs (photo replay, screen replay where applicable)
  
Acceptance criteria should be defined before release (example targets below in **2.6 Test metrics**).
  
#### 2.2.4 High-order testing
  
High-order tests include:
  
- **Performance testing:** p95/p99 API latency for registration and attendance capture endpoints; throughput under concurrent sessions.
- **Reliability testing:** error budgets (5xx rates), background processing stability, retry behavior.
- **Security testing:** authz checks, JWT expiry/rotation, rate limiting assumptions, upload validation, dependency scanning.
- **A/B testing (experiment):** controlled rollout comparing Variant A vs Variant B on pre-defined metrics and guardrails.
  
### 2.3 Testing resources and staffing
  
- **Test owner:** QA/Engineering lead (responsible for test execution and sign-off).
- **Backend engineer(s):** write/maintain unit + integration tests; fix defects.
- **Frontend engineer(s):** UI test automation; device/browser validation.
- **ML/Applied engineer(s):** model-quality evaluation, threshold selection, liveness attack testing.
  
Optional specialized support:
  
- Security reviewer (threat model + basic pen test of auth/upload endpoints).
- Data steward (consent, retention, access policies for facial data).
  
### 2.4 Test work products
  
- Test plan and procedure (this document)
- Test cases (unit/integration/validation checklists)
- Automated test suites + reports (CI artifacts where available)
- A/B experiment design, event schema, and analysis report
- Release sign-off checklist and defect logs
  
### 2.5 Test record keeping
  
- Central test run log (date, build/version, environment, tester, results).
- Defects tracked in an issue tracker with severity and reproduction steps.
- A/B experiment telemetry stored in:
  - application logs (backend)
  - analytics/event tables (e.g., Supabase tables) with experiment assignment + outcomes
  
Minimum fields for experiment events:
  
- `experiment_name`, `variant`, `user_role` (lecturer/student), `device_class`, `timestamp`
- outcome fields (e.g., `liveness_pass`, `recognition_success`, `latency_ms`, `error_code`)
  
### 2.6 Test metrics
  
**Functional**
  
- API success rate per endpoint (2xx / total)
- E2E flow completion rate (registration, attendance capture)
  
**Biometric / liveness quality (offline + online)**
  
- **FRR** (False Reject Rate) and **FAR** (False Accept Rate) at configured threshold(s)
- **TPR/FPR** and ROC curve on curated test data (where available)
- Liveness:
  - **APCER** (attack presentations misclassified as bona fide)
  - **BPCER** (bona fide misclassified as attack)
  
**Performance & reliability**
  
- p50/p95/p99 latency per critical endpoint (registration, attendance capture)
- CPU/memory utilization on the deployed backend
- 4xx/5xx rate, timeout rate, background job failure rate
  
**A/B success metric examples (choose before running)**
  
- Primary: `attendance_success_rate` (recognized & recorded / attempts)
- Secondary: `registration_completion_rate`, `median_capture_time_s`
- Guardrails: `false_reject_proxy_rate`, `support_tickets_rate`, `p95_latency_ms`, `crash_rate`
  
### 2.7 Testing tools and environment
  
**Backend**
  
- Local/dev: FastAPI + test Supabase project or local Postgres mirror
- Test runner: `pytest` (recommended), HTTP client `httpx` (recommended)
  
**Frontend**
  
- Unit/component tests: `vitest` + React Testing Library (recommended)
- E2E: Playwright or Cypress (recommended) with camera/video mocking where feasible
  
**Performance**
  
- k6 or Locust for load tests (recommended)
  
**Security**
  
- Static checks: Bandit/Semgrep (recommended)
- Dependency scanning via standard ecosystem tools (npm audit/pip-audit) (recommended)
  
**Test data**
  
- Synthetic/consented datasets for images/videos (labelled by lighting/device/pose)
- Spoof media for liveness testing (photo/screen replay) stored securely
  
### 2.8 Test schedule
  
Example schedule (adjust per release):
  
- Week 1: unit test coverage for high-risk modules; define A/B hypothesis + metrics + event schema
- Week 2: integration tests for API routes; validation test checklist; baseline performance run
- Week 3: staged rollout A/B test (10% → 50% traffic) with monitoring and daily checks
- Week 4: analyze results; finalize thresholds; release sign-off
  
---
  
## 3.0 Test Procedure
  
### 3.1 Software (SCI’s) to be tested
  
- Backend: `facial_recognition_backend/app/` (routers, services, utils), `migrations/`
- Frontend: `facial_recognition_frontend/src/` (pages, components, store, utils)
  
### 3.2 Testing procedure
  
#### 3.2.1 Unit test cases
  
This section lists recommended unit test areas (test cases are examples; expand as needed).
  
##### Component i: `app/utils/security.py`
  
**Stubs/drivers**
  
- Stub JWT secret/time provider if needed for deterministic expiration tests.
  
**Test cases**
  
- Password hashing produces non-plaintext; verify correct password passes, wrong fails.
- JWT encode/decode round-trip; invalid signature fails; expired token fails.
  
**Purpose**
  
- Prevent auth regressions and security weaknesses.
  
**Expected results**
  
- All validations behave as specified; failures return appropriate errors.
  
##### Component i: `app/services/matching.py`
  
**Stubs/drivers**
  
- Provide deterministic embeddings and thresholds (no model inference).
  
**Test cases**
  
- Similarity scoring returns expected values for known vectors.
- Threshold decision: accept when score ≥ threshold; reject otherwise.
- Edge cases: empty candidate set, NaN/invalid vector input.
  
**Purpose**
  
- Ensure recognition decisions are stable and explainable.
  
**Expected results**
  
- Deterministic accept/reject behavior and safe handling of invalid inputs.
  
##### Component i: Frontend API client `src/utils/api.js`
  
**Stubs/drivers**
  
- Mock fetch/axios layer; simulate 2xx/4xx/5xx responses and network timeouts.
  
**Test cases**
  
- Correct headers (JWT) attached when logged in.
- Error handling displays correct UI messages and does not leak sensitive info.
  
**Expected results**
  
- Stable network behavior under expected and failure conditions.
  
#### 3.2.2 Integration testing
  
##### 3.2.2.1 Testing procedure for integration
  
1) Bring up backend against a test Supabase/Postgres instance.  
2) Run migrations in `facial_recognition_backend/migrations/`.  
3) Seed minimal data (lecturer account, unit, sample students).  
4) Execute API route flows:
   - login → create unit → register student (liveness pass) → create attendance session → submit attendance capture → verify report output  
5) Verify logs and stored database state match expected outcomes.
  
#### 3.2.3 Validation testing (E2E / UAT)
  
1) Run the frontend connected to the test backend.  
2) Validate supported browser(s) and representative device classes.  
3) Execute user journeys:
   - Lecturer registration/login/reset password  
   - Student registration + liveness  
   - Attendance session start → capture → session close → report  
4) Verify usability, error messages, and recovery from camera/network issues.
  
#### 3.2.4 A/B testing procedure (experiment)
  
**Experiment definition**
  
- **Name:** `liveness_or_recognition_variant` (example)
- **Population:** consenting users in pilot environment (or a staged production rollout)
- **Randomization unit:** user ID (preferred) or device/session ID
- **Assignment:** 50/50 split unless risk requires smaller initial treatment
  
**Variants (example)**
  
| Variant | Description |
|---|---|
| A (Control) | Current liveness + recognition pipeline and UI flow |
| B (Treatment) | Updated liveness checks and/or adjusted recognition threshold / improved capture UX |
  
**Execution steps**
  
1) Implement deterministic assignment and persist it (so users stay in the same variant).  
2) Emit analytics events for each attempt and outcome (success/fail + latency + errors).  
3) Run a staged rollout (e.g., 10% for 48h, then 50% if guardrails are healthy).  
4) Monitor guardrails daily; stop the test if thresholds are breached.  
5) After reaching sample size/time, run analysis and document a decision (ship B / iterate / rollback).
  
**Stopping rules (examples; set before launch)**
  
- Guardrail breach: p95 latency +20% vs control for 24h, or error rate +1% absolute.
- Clear win: primary metric improves by ≥X% with no guardrail breaches.
  
