# 📧 Email Automation

A Python-based email automation tool that scrapes recruiter contact information, enriches it using the Hunter.io API, and sends personalized outreach emails via SendGrid. Built with FastAPI and backed by PostgreSQL and Redis, the entire stack runs seamlessly with Docker Compose.

---

## 🚀 Features

- **Recruiter Discovery** — Scrapes and stores recruiter data from the web
- **Email Enrichment** — Finds professional email addresses using the [Hunter.io](https://hunter.io) API
- **Automated Outreach** — Sends personalized emails at scale via [SendGrid](https://sendgrid.com)
- **H1B Sponsor Lookup** — Checks company H1B sponsorship history via h1bgrader.com
- **PostgreSQL Storage** — Persists recruiter records and email history
- **Redis Integration** — Supports queuing and caching
- **Dockerized** — One-command setup with Docker Compose

---

## 🛠️ Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Language    | Python 3.x                        |
| Web Framework | FastAPI + Uvicorn               |
| Database    | PostgreSQL 15                     |
| Cache/Queue | Redis 7                           |
| Email API   | SendGrid                          |
| Email Enrichment | Hunter.io                    |
| ORM         | SQLAlchemy                        |
| Containerization | Docker + Docker Compose      |

---

## 📁 Project Structure

```
Email_Automation/
├── app/                  # Application source code
├── .env.example          # Environment variable template
├── .dockerignore
├── .gitignore
├── Dockerfile
├── docker-compose.yml    # Multi-service container setup
├── init.sql              # Database initialization script
└── requirements.txt      # Python dependencies
```

---

## ⚙️ Setup & Installation

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose installed
- A [Hunter.io](https://hunter.io) API key
- A [SendGrid](https://sendgrid.com) API key

### 1. Clone the Repository

```bash
git clone https://github.com/aramineni28/Email_Automation.git
cd Email_Automation
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
HUNTER_API_KEY=your_hunter_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
DATABASE_URL=postgresql://postgres:postgres@db:5432/recruiters
H1B_LOOKUP_URL=https://h1bgrader.com/
```

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

This will spin up three services:
- **app** — the Python automation runner
- **db** — PostgreSQL database (port `5432`)
- **redis** — Redis instance (port `6379`)

---

## 🔑 Environment Variables

| Variable           | Description                                      |
|--------------------|--------------------------------------------------|
| `HUNTER_API_KEY`   | API key for Hunter.io email enrichment           |
| `SENDGRID_API_KEY` | API key for sending emails via SendGrid          |
| `DATABASE_URL`     | PostgreSQL connection string                     |
| `H1B_LOOKUP_URL`   | Base URL for H1B sponsorship lookup              |

---

## 📦 Dependencies

Key packages from `requirements.txt`:

- `fastapi` + `uvicorn` — API framework and server
- `sqlalchemy` + `psycopg2-binary` — Database ORM and PostgreSQL driver
- `sendgrid` — Email delivery
- `requests` + `beautifulsoup4` — Web scraping
- `pandas` + `numpy` — Data processing
- `python-dotenv` — Environment variable management
- `pydantic` — Data validation

---

## 🐳 Docker Services

| Service         | Image          | Port   |
|-----------------|----------------|--------|
| `recruiter_app` | Custom (Dockerfile) | —  |
| `recruiter_db`  | postgres:15    | 5432   |
| `recruiter_redis` | redis:7      | 6379   |

---

## 📝 Notes

- Make sure your SendGrid sender email is verified before running outreach campaigns.
- Hunter.io has a free tier with limited monthly lookups — monitor your usage.
- The `init.sql` file runs automatically on first database startup to create the required schema.

---

## 📄 License

This project is open source. See the repository for details.
