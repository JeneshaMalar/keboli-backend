# FastAPI API Documentation

**Version:** 0.1.0

**Generated on:** 2026-03-12 14:04:15


---
API Documentation
---


## `/api/auth/login`

### POST: Login

**Description:** 

**Tags:** auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/auth/register-org`

### POST: Register Org

**Description:** 

**Tags:** auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/auth/logout`

### POST: Logout

**Description:** 

**Tags:** auth


**Responses:**

- `200` — Successful Response


---


## `/api/auth/me`

### GET: Me

**Description:** 

**Tags:** auth


**Responses:**

- `200` — Successful Response


---


## `/api/health`

### GET: Health

**Description:** 

**Tags:** 


**Responses:**

- `200` — Successful Response


---


## `/api/assessment/`

### POST: Create New Assessment

**Description:** 

**Tags:** auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/assessment/create-with-file`

### POST: Create Assessment With File

**Description:** 

**Tags:** auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/assessment/org-assessments`

### GET: Get Org Assessments

**Description:** 

**Tags:** auth


**Responses:**

- `200` — Successful Response


---


## `/api/assessment/{assessment_id}`

### GET: Get Assessment

**Description:** 

**Tags:** auth


**Parameters:**

- `assessment_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### PUT: Update Assessment

**Description:** 

**Tags:** auth


**Parameters:**

- `assessment_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### DELETE: Delete Assessment

**Description:** 

**Tags:** auth


**Parameters:**

- `assessment_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/assessment/{assessment_id}/skills`

### PATCH: Update Assessment Skills Internal

**Description:** 

**Tags:** auth


**Parameters:**

- `assessment_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/assessment/{assessment_id}/toggle`

### PATCH: Toggle Assessment

**Description:** 

**Tags:** auth


**Parameters:**

- `assessment_id` (path) — 

- `is_active` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/candidate/`

### POST: Create Candidate

**Description:** 

**Tags:** candidate


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/candidate/org-candidates`

### GET: Get Org Candidates

**Description:** 

**Tags:** candidate


**Responses:**

- `200` — Successful Response


---


## `/api/candidate/{candidate_id}`

### DELETE: Delete Candidate

**Description:** 

**Tags:** candidate


**Parameters:**

- `candidate_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/candidate/bulk-upload`

### POST: Bulk Upload Candidates

**Description:** 

**Tags:** candidate


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/invitation/`

### POST: Create Invitation

**Description:** 

**Tags:** invitation


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/invitation/org-invitations`

### GET: Get Org Invitations

**Description:** 

**Tags:** invitation


**Responses:**

- `200` — Successful Response


---


## `/api/invitation/{invitation_id}/revoke`

### PATCH: Revoke Invitation

**Description:** 

**Tags:** invitation


**Parameters:**

- `invitation_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/invitation/validate/{token}`

### GET: Validate Token

**Description:** 

**Tags:** invitation


**Parameters:**

- `token` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/evaluation/transcript/{session_id}`

### GET: Get Transcript For Eval

**Description:** 

**Tags:** evaluation


**Parameters:**

- `session_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/evaluation/session/{session_id}`

### GET: Get Session Details For Eval

**Description:** 

**Tags:** evaluation


**Parameters:**

- `session_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/evaluation/report/{session_id}`

### POST: Post Evaluation Report

**Description:** 

**Tags:** evaluation


**Parameters:**

- `session_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### GET: Get Evaluation Report

**Description:** 

**Tags:** evaluation


**Parameters:**

- `session_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### PATCH: Update Evaluation Report

**Description:** 

**Tags:** evaluation


**Parameters:**

- `session_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/evaluation/trigger/{session_id}`

### POST: Trigger Evaluation

**Description:** 

**Tags:** evaluation


**Parameters:**

- `session_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/livekit/token`

### POST: Get Token

**Description:** 

**Tags:** livekit


**Parameters:**

- `invitation_token` (query) — The invitation token


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/livekit/transcript/{session_id}/append`

### POST: Append Transcript

**Description:** 

**Tags:** livekit


**Parameters:**

- `session_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/livekit/session/{session_id}/complete`

### POST: Complete Session

**Description:** 

**Tags:** livekit


**Parameters:**

- `session_id` (path) — 

- `auto_evaluate` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/livekit/session/heartbeat/{session_id}`

### POST: Heartbeat

**Description:** 

**Tags:** livekit


**Parameters:**

- `session_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/livekit/session/{session_id}/status`

### GET: Get Session Status

**Description:** Check if a session has been completed by the backend.
Frontend polls this as a fallback when the LiveKit data message might not arrive.

**Tags:** livekit


**Parameters:**

- `session_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/api/logs/`

### POST: Create Log

**Description:** 

**Tags:** Logs


**Request Body Example:**


**Responses:**

- `201` — Successful Response

- `422` — Validation Error


---


## `/api/notifications/`

### GET: Get Notifications

**Description:** 

**Tags:** notifications


**Responses:**

- `200` — Successful Response


---


## `/api/notifications/{notification_id}/read`

### PATCH: Mark Read

**Description:** 

**Tags:** notifications


**Parameters:**

- `notification_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---
