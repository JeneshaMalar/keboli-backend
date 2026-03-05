# Backend

This is the **backend service** built using **FastAPI**.
It provides REST APIs for the application and runs using **Uvicorn ASGI server**.

---

## 🚀 Tech Stack

* FastAPI
* Uvicorn
* Python
* Pydantic
* SQLAlchemy / Database (if applicable)

---

## 📦 Prerequisites

Make sure you have the following installed:

* Python **3.9+**
* pip


Check your installation:

```bash
python --version
pip --version
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/JeneshaMalar/keboli-backend.git
cd backend
```

---

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate the environment:

**Mac/Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 3. Install dependencies using `uv`

This project uses **uv** for fast Python package management and environment handling.

Install `uv` if you don't have it:

```bash
pip install uv
```

or (recommended)

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

---

### 4. Install project dependencies

Install dependencies defined in `pyproject.toml`:

```bash
uv sync
```

This will:

* Create a virtual environment automatically
* Install all dependencies from `pyproject.toml`
* Lock them in `uv.lock`

---



## ▶️ Run the Development Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn src.main:app --reload
```

The API will start at:

```
http://127.0.0.1:8000
```

---

## 📖 API Documentation

FastAPI automatically generates interactive API documentation.

Swagger UI:

```
http://127.0.0.1:8000/docs
```

ReDoc:

```
http://127.0.0.1:8000/redoc
```

---



## 🔧 Environment Variables

Create a `.env` file in the root directory if your project uses environment variables.

Example:

```
DATABASE_URL=postgresql+asyncpg://<USER>:<PASSWORD>@localhost:5432/<DB NAME>
SECRET_KEY=supersecret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DEEPGRAM_API_KEY=<YOUR API KEY>
GROQ_API_KEY=<YOUR API KEY>
GROQ_MODEL=llama-3.3-70b-versatile


LIVEKIT_URL=wss://<YOUR PROJECT>.livekit.cloud
LIVEKIT_API_KEY=<YOUR API KEY>
LIVEKIT_API_SECRET=<YOUR SECRET KEY>
```

---

