# 🇮🇳 ShramMitra
### Empowering India's Gig Workers Through Digital Access

ShramMitra is a full-stack web platform designed to help India's gig workers, especially delivery partners and cab drivers, discover government welfare schemes, check eligibility, manage documents, track applications, and raise grievances through a single digital platform.

Our mission is to simplify access to government benefits and social security by making the process more accessible, transparent, and user-friendly.

---

## 🎯 Problem Statement

Many gig workers are unaware of the government schemes, insurance benefits, and social security programs available to them.

Even when workers know about these benefits, complicated application procedures, documentation requirements, and a lack of guidance make accessing them difficult.

**ShramMitra bridges this gap between government welfare schemes and the workers who need them.**

---

## 💡 Our Solution

ShramMitra provides a centralized digital platform where gig workers can:

- 🔍 Discover relevant government welfare schemes.
- ✅ Check eligibility based on their personal and professional profiles.
- 📄 Upload and securely manage required documents.
- 📝 Get guidance through the scheme application process.
- 📊 Track application status and progress.
- 🔔 Receive guidance on pending actions and missing documents.
- ⚖️ Raise grievances and monitor their resolution.
- 📰 Discover updates about government schemes and benefits.

---

## ✨ Key Features

### 1. User Authentication
- Secure user registration and login.
- Password hashing using Argon2.
- JWT-based authentication.
- Role-based access control for workers and administrators.

### 2. Government Scheme Discovery
- Central and state government welfare schemes.
- Verified scheme information from official sources.
- Scheme categories and detailed descriptions.
- A flexible foundation for adding new states and worker categories.

### 3. Eligibility Assessment
- Rule-based eligibility evaluation.
- Matching schemes against worker profiles.
- Identification of missing requirements.
- A foundation for future personalized recommendations.

### 4. Application Tracking
- Track scheme applications.
- Monitor application status.
- Store application reference numbers.
- Identify pending actions and required documents.

### 5. Document Vault
- Centralized document management.
- Reuse documents across applications.
- A foundation for secure document storage and access controls.

### 6. Grievance Management
- Submit grievances related to applications and benefits.
- Track grievance status.
- Monitor pending grievances and follow-up actions.

### 7. Administrative Verification
- Authorized administrators can verify scheme information.
- Maintain scheme verification history.
- Track changes to verification status and scheme versions.

---

## 🛠️ Technology Stack

### Frontend
- React
- TypeScript
- Vite
- HTML5
- CSS3

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- JWT Authentication
- Argon2 Password Hashing

### Database
- PostgreSQL
- SQLite for automated tests

### Development Tools
- Git
- GitHub
- Visual Studio Code
- Pytest
- REST API Documentation with Swagger UI

---

## 🏗️ System Architecture

```text
                 ┌──────────────────────┐
                 │      Gig Worker      │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │   React + TypeScript │
                 │      Frontend        │
                 └──────────┬───────────┘
                            │ HTTP / REST API
                            ▼
                 ┌──────────────────────┐
                 │   FastAPI Backend    │
                 ├──────────────────────┤
                 │ Authentication       │
                 │ Eligibility Engine   │
                 │ Scheme Management    │
                 │ Application Tracking │
                 │ Grievance Management │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │     PostgreSQL       │
                 │       Database       │
                 └──────────────────────┘