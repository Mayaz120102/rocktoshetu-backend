# 🩸 RoktoShetu Backend

A FastAPI-powered backend for **RoktoShetu**, a blood connection platform designed to connect blood donors with people in urgent need of blood.

RoktoShetu aims to make the process of finding and connecting with blood donors easier, faster, and more organized. This repository contains the backend/API of the platform, providing server-side logic, authentication, database communication, and RESTful APIs required by the frontend application.

## 🌐 Links

* 🎨 **Frontend Application:** <https://roktoshetu-frontend-v1.vercel.app/>

* 💻 **Frontend Repository:** [Mayaz120102/roktoshetu-frontend-v1](https://github.com/Mayaz120102/roktoshetu-frontend-v1)

* ⚙️ **Backend Repository:** [Mayaz120102/rocktoshetu-backend](https://github.com/Mayaz120102/rocktoshetu-backend)

## 🚀 Features

### 🔐 Authentication & Security

* User registration and authentication

* JWT-based secure authentication

* Password hashing and secure credential handling

* Authentication-ready API architecture

### 👤 User Management

* User registration and profile lifecycle management

* Blood group identification and storage

* Location-related information for donor connection

### 🩸 Blood Request Management

* Creation and management of blood requests

* Tracking request status

* Connecting blood requests with potential donors

### 🗄️ Database

* **PostgreSQL:** Relational database storage

* **SQLAlchemy ORM:** Database abstraction layer and query building

### 📧 Email Validation

* Email validation integrated into user and authentication infrastructure

## 🛠️ Tech Stack

### Backend

* **Python 3.13+**

* **FastAPI**

* **Pydantic**

* **SQLAlchemy**

### Database

* **PostgreSQL**

* **SQLAlchemy ORM**

### Authentication & Security

* JWT (JSON Web Tokens)

* Python-JOSE

* Passlib & bcrypt

* Email validation

### DevOps & Tools

* **Docker**

* **Linux**

* **Git & GitHub**

* **uv** (Package & Environment Manager)

## 📁 Project Structure

```
rocktoshetu-backend/
│
├── app/
│   ├── ...
│   │
│   └── ...
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── uv.lock

```

The project follows a modular backend structure so that features such as authentication, database operations, models, schemas, and API routes can be developed independently.

## ⚙️ Requirements

Before running the project, make sure you have:

* **Python 3.13+**

* **PostgreSQL**

* **Git**

* **Docker** (optional, for containerized environment)

## 🔧 Installation

### 1. Clone the repository

```
git clone https://github.com/Mayaz120102/rocktoshetu-backend.git
cd rocktoshetu-backend

```

### 2. Create a virtual environment

**Using `uv` (recommended):**

```
uv venv

```

**Using standard `venv`:**

```
python -m venv venv

```

Activate the virtual environment:

* **Linux / macOS:**

  ```
  source .venv/bin/activate  # or source venv/bin/activate
  
  ```

* **Windows:**

  ```
  .venv\Scripts\activate     # or venv\Scripts\activate
  
  ```

### 3. Install dependencies

**Using `uv`:**

```
uv sync

```

**Using `pip`:**

```
pip install -r requirements.txt
# Or for editable installation:
pip install -e .

```

### 4. Configure environment variables

Create a `.env` file based on the provided example:

```
cp .env.example .env

```

Then configure the required database and authentication settings:

```
DATABASE_URL=postgresql://username:password@localhost:5432/roktoshetu
SECRET_KEY=your-secret-key
ALGORITHM=HS256

```

> ⚠️ **Security Note:** Never commit your actual `.env` file or secret keys to GitHub.

## ▶️ Running the Backend

Start the FastAPI development server using `uv`:

```
uv run fastapi dev app/main.py

```

The API will be available at:
`http://127.0.0.1:8000`

## 📚 API Documentation

FastAPI automatically provides interactive API documentation out of the box:

* **Swagger UI:** <http://127.0.0.1:8000/docs>

* **ReDoc:** <http://127.0.0.1:8000/redoc>

## 🐳 Running with Docker

### Build the Docker image:

```
docker build -t roktoshetu-backend .

```

### Run the container:

```
docker run -p 8000:8000 roktoshetu-backend

```

For production, the application can be connected to a PostgreSQL instance through environment variables.

## 🔑 Authentication Flow

The backend uses token-based authentication.

```
User
  │
  ▼
Register / Login
  │
  ▼
FastAPI Backend
  │
  ├── Validate credentials
  │
  ├── Hash / verify password
  │
  └── Generate JWT
          │
          ▼
       Client
          │
          ▼
   Authenticated API Requests

```

## 🔄 Application Architecture

```
                  ┌────────────────────┐
                  │    React Frontend  │
                  └─────────┬──────────┘
                            │
                            │ HTTP / REST API
                            ▼
                  ┌────────────────────┐
                  │    FastAPI API     │
                  └─────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        Authentication   Business      Validation
                         Logic
              │             │
              └─────────────┼─────────────┘
                            ▼
                  ┌────────────────────┐
                  │    SQLAlchemy      │
                  │       ORM          │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │    PostgreSQL      │
                  └─────────┬──────────┘

```

## 🛣️ Future Work

RoktoShetu is an ongoing project with several planned future improvements:

* 🩸 **Advanced Blood Request System:** Request priority levels, expiration, status tracking, urgent requests, donor-request matching, and request history.

* 📍 **Location-Based Donor Matching:** Distance-based donor filtering, city/area search, and nearby urgent request discovery.

* 🔔 **Notifications:** Email, push, and in-app notifications for request alerts, donor matches, and updates.

* 🩸 **Donor Availability:** Status toggles (`Available` ↔ `Temporarily Unavailable`).

* ⭐ **Donor Verification & Reputation:** Verified donor profiles, donation history, and reliability tracking.

* 📊 **Admin Dashboard:** Platform statistics, user and request oversight, and monitoring.

* 🛡️ **Improved Security:** Refresh token rotation, rate limiting, account lockout protection, and audit logging.

* 🧪 **Automated Testing:** Unit tests, integration tests, and API tests with `pytest`.

* 🚀 **CI/CD:** GitHub Actions integration for automated testing, code checks, and deployment.

* 📈 **Monitoring & Logging:** Structured application logs, error tracking, health checks, and performance metrics.

## 🤝 Contributing

Contributions, suggestions, and feedback are welcome!

1. Fork the repository

2. Create a new branch (`git checkout -b feature/your-feature`)

3. Make your changes

4. Commit your changes (`git commit -m "Add: your feature"`)

5. Push the branch (`git push origin feature/your-feature`)

6. Open a Pull Request

## 👨‍💻 Developer

**Abrar Mayaz**

Computer Science & Engineering Student

*International Islamic University Chittagong*

* 🌐 **GitHub:** [@Mayaz120102](https://github.com/Mayaz120102)

* 💼 **LinkedIn:** [Abrar Mayaz](https://www.linkedin.com/in/abrar-mayaz-53b7b2282/)

* 🏆 **Codeforces:** [mayaz1202](https://codeforces.com/profile/mayaz1202)

## 📄 License

This project is currently under development. License information will be added as the project evolves.
