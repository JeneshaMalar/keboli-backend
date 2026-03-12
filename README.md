# Keboli - AI Interview Bot 

Backend service for the **AI Interview Bot platform**, responsible for managing interview sessions, candidate invitations, AI evaluation, and recruiter workflows.

This backend is built with **FastAPI**, uses **PostgreSQL** for data storage, integrates **LiveKit** for real-time communication, and connects with **LLM services** for automated interview evaluation.

---

# 1. Project Information

## Overview

The AI Interview Bot backend powers an automated interview system where recruiters can create assessments and invite candidates to AI-driven interviews. Candidates join sessions through secure links and interact with an AI interviewer. Their responses are processed and evaluated automatically using large language models.

The backend handles:

* recruiter and candidate management
* interview assessment configuration
* invitation generation
* real-time interview session orchestration
* response collection
* AI-based evaluation
* result storage

---

## Key Features

* RESTful API built with **FastAPI**
* Asynchronous database operations
* AI-driven response evaluation
* Secure candidate invitation links
* Integration with LiveKit for real-time sessions
* Docker-based service orchestration
* Email-based candidate invitation system

---

## Technology Stack

| Layer                   | Technology             |
| ----------------------- | ---------------------- |
| Backend Framework       | FastAPI                |
| Database                | PostgreSQL             |
| ORM                     | SQLAlchemy (Async)     |
| AI Integration          | LangGraph / Groq       |
| Real-time Communication | LiveKit                |
| Email Service           | SendGrid               |
| Containerization        | Docker                 |
| Dependency Management   | uv                     |

---

# 2. Architecture Overview

The backend is designed as a **modular API service** that interacts with multiple external services to conduct AI-powered interviews.

## High Level Architecture

```
                +----------------------+
                |      Frontend        |
                |  (React Application) |
                +----------+-----------+
                           |
                           |
                    REST API Calls
                           |
                           v
                +----------------------+
                |     FastAPI Backend  |
                |                      |
                |  - Auth APIs        |
                |  - Assessment APIs  |
                |  - Candidate APIs   |
                |  - Interview APIs   |
                |  - Evaluation APIs  |
                +----------+-----------+
                           |
           ----------------------------------------
           |                    |                 |
           v                    v                 v

   +-------------+     +---------------+     +-------------+
   | PostgreSQL  |     | LiveKit + LLM |     |  LLM Engine |
   | Database    |     | (Interview)   |     | (Evaluation)|
   +-------------+     +---------------+     +-------------+
           |
           v
     +------------+
     | SendGrid   |
     | Email API  |
     +------------+
```

---

## Service Interaction Flow

### 1. Recruiter Creates Assessment

The recruiter uses the frontend dashboard to create an interview assessment.

Frontend → FastAPI → PostgreSQL

---

### 2. Candidate Invitation

The backend generates a **secure invitation link** and sends it via email.

FastAPI → SendGrid → Candidate Email

---

### 3. Candidate Starts Interview

The candidate opens the invitation link and joins an interview session.

Frontend → FastAPI → LiveKit

The backend generates a **LiveKit token** to allow the candidate to join the interview room.

---

### 4. Interview Interaction

The AI interviewer asks questions and records candidate responses.

LiveKit handles:

* audio/video communication
* real-time streaming

The backend manages:

* session lifecycle
* response storage

---

### 5. AI Evaluation

Candidate responses are processed by an LLM service.

FastAPI → LLM Adapter → Evaluation Engine

The evaluation result includes:

* score
* feedback
* analysis

---

### 6. Result Storage

Evaluation results are stored in PostgreSQL.

Recruiters can view candidate performance via the dashboard.

---

# 3. Running the Backend Locally

## Prerequisites

Make sure the following are installed:

* Python 3.10+
* PostgreSQL
* Docker (optional but recommended)
* Git

---



### Step 1 – Clone Repository

```bash
git clone https://github.com/JeneshaMalar/keboli-backend.git
cd keboli-backend
```

---

### Step 2 – Create Virtual Environment

```
python -m venv venv
```

Activate environment:

Mac/Linux

```
source venv/bin/activate
```

Windows

```
venv\Scripts\activate
```

---

### Step 3 – Configure Environment Variables

Create a `.env` file.

Example:

```
DATABASE_URL=postgresql+asyncpg://<USER>:<PASSWORD>@localhost:5432/<DB NAME>
SECRET_KEY=supersecret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DEEPGRAM_API_KEY=<YOUR API KEY>
GROQ_API_KEY=<YOUR API KEY>
GROQ_MODEL=llama-3.3-70b-versatile
SENDGRID_API_KEY=<YOUR API KEY>
SENDGRID_FROM_EMAIL=jeneshamalar@gmail.com

LIVEKIT_URL=wss://<YOUR PROJECT>.livekit.cloud
LIVEKIT_API_KEY=<YOUR API KEY>
LIVEKIT_API_SECRET=<YOUR SECRET KEY>
```

---

### Step 4 – Install Dependencies

```
uv sync
```

---

### Step 5 – Run Database

Make sure PostgreSQL is running locally.

---

### Step 6 – Apply Database Migrations

```
alembic upgrade head
```

---

### Backend Entry Point

```
app/main.py
```

FastAPI server is launched using:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

### Access API

```
http://localhost:8000
```

Swagger documentation:

```
http://localhost:8000/docs
```

---


# 6. Environment Variables

| Variable           | Description                  |
| ------------------ | ---------------------------- |
| DATABASE_URL       | PostgreSQL connection string |
| SENDGRID_API_KEY   | Email service API key        |
| LIVEKIT_API_KEY    | LiveKit authentication key   |
| LIVEKIT_API_SECRET | LiveKit secret               |
| LIVEKIT_URL        | LiveKit server URL           |
| GROQ_API_KEY       | LLM service API key          |

---

# 7. Future Improvements

Potential enhancements include:

* Resume-based question generation
* Multi-language AI support
* Third party ATS integration
* Proctoring

---

# Author

**Jenesha Malar**

Keboli – Backend Development


