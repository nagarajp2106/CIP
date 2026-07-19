# AI Banking Customer Insights Platform

[![GitHub stars](https://img.shields.io/github/stars/nagarajp2106/CIP?style=social)](https://github.com/nagarajp2106/CIP)
[![GitHub license](https://img.shields.io/github/license/nagarajp2106/CIP)](https://github.com/nagarajp2106/CIP/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.33%2B-ff4b4b)](https://streamlit.io/)

---

## 🎯 Project Overview

**AI Banking Customer Insights** is a modern, end‑to‑end analytics platform for retail banking. It provides:
- **Secure data upload & validation** – ingest CSVs, enforce relational integrity.
- **AI‑powered analytics** – churn prediction, customer lifetime value (CLV), product recommendation, deposit forecasting, and automated business insights.
- **Interactive dashboards** – rich visualisations built with Streamlit & Plotly.
- **Professional reporting** – multi‑sheet Excel workbooks with styled tables and native charts.
- **Role‑based access control** – Admin, Bank Manager, and Data Analyst permissions.

All components live in a single, self‑contained Python codebase using SQLite as the database, making it easy to run locally or containerise for production.

---

## 📦 Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Streamlit (Python) – custom CSS, icon set, responsive layout |
| **Backend** | Python 3.10+, SQLite (`sqlite3`), Pandas, NumPy |
| **Machine Learning** | Scikit‑learn (Random Forest, Gradient Boosting, KMeans) – models stored as Pickle |
| **Authentication** | JWT (HS256) & BCrypt password hashing |
| **Reporting** | Openpyxl – multi‑sheet Excel with embedded charts |
| **Styling** | Modern UI palette from `config.COLORS`, glass‑morphism style, smooth micro‑animations |
| **Deployment** | Streamlit server (`streamlit run app.py`) – can be containerised (Docker) |

---

## 🏗️ Architecture & Design

```
User (browser) → Streamlit UI → Python Business Logic
    ├─ utils/* – preprocessing, feature engineering, model inference
    ├─ database.py – SQLite schema, synthetic data seeding
    ├─ authentication.py / jwt_handler.py – login, token handling
    ├─ pages/*.py – individual Streamlit pages (Dashboard, Upload, Analytics …)
    ├─ reports/reports.py – Excel report generator
    └─ assets/ – CSS, icons
```

The application follows a **service‑layer** pattern with a clear separation between UI, data access, and analytics. Role‑based access is enforced via the `PAGE_ACCESS` map in `config.py`.

---

## 📁 Repository Structure

```
CIP/
├─ .git/                # Git history
├─ .gitignore
├─ .streamlit/          # Streamlit config
├─ app.py                # Entry point, page config, navigation
├─ authentication.py     # Login UI & session handling
├─ config.py             # Global constants, paths, colours, JWT settings
├─ database/             # SQLite file (banking.db)
├─ database.py           # Schema creation, synthetic data seeding
├─ datasets/             # CSV files (seed + synthetic samples)
├─ jwt_handler.py        # JWT encode/decode helpers
├─ models/               # Pickled ML models (segmentation.pkl, churn.pkl, …)
├─ pages/                # Streamlit page modules
├─ reports/              # (optional) custom report templates
├─ requirements.txt      # Python dependencies
├─ scratch/              # Temporary scripts (audit, data fixes)
├─ utils/                # Core utilities (auth, preprocessing, prediction, …)
└─ assets/               # style.css, custom icons
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or newer
- Git
- (Optional) Docker for containerised deployment

### Installation
```bash
# Clone the repository
git clone https://github.com/nagarajp2106/CIP.git
cd CIP

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
streamlit run app.py
```
The app will start on `http://localhost:8501`. Use the demo credentials from `config.py`:
- **admin** – `admin123`
- **manager** – `manager123`
- **analyst** – `analyst123`

---

## 📊 Features at a Glance
- **Dashboard** – KPI cards for customers, accounts, transactions, loans.
- **Data Upload** – CSV validation, foreign‑key checks, automatic insertion.
- **Churn Prediction** – Random Forest model with per‑customer scores.
- **CLV Estimation** – Gradient Boosting regression for lifetime value.
- **Customer Segmentation** – KMeans clustering visualised on scatter plots.
- **Product Recommendation** – Content‑based suggestions.
- **Deposit Forecast** – Time‑series model for future deposits.
- **AI Business Insights** – Auto‑generated textual summary of key trends.
- **Export Reports** – Multi‑sheet Excel workbook (Summary, Data, Charts) with native Excel charts.
- **Audit Logging** – Every action recorded in `audit_logs`.
- **Role‑Based UI** – Admin, Bank Manager, Data Analyst tailored navigation.

---

## 🛠️ Development & Contribution
1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** and ensure they pass the built‑in validation scripts (`scratch/audit_datasets.py`).
3. **Run the test suite** (currently manual, see `scratch/` scripts).
4. **Commit & push**
   ```bash
   git add .
   git commit -m "Brief description of your change"
   git push origin feature/your-feature-name
   ```
5. Open a Pull Request on GitHub.

Please adhere to the existing code style (PEP‑8) and update documentation where appropriate.

---

## 🧪 Testing & Validation
- **Dataset audit** – `scratch/audit_datasets.py` validates schema, FK integrity, and business rules.
- **End‑to‑end insertion test** – `scratch/test_e2e_insertion.py` confirms the whole pipeline loads without errors.
- **Model sanity checks** – `scratch/verify_all.py` verifies EMI calculations and model outputs.

Add pytest suites for future automated testing.

---

## 📦 Deployment Guide
### Docker (recommended for production)
```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
Build & run:
```bash
docker build -t ai-banking-insights .
docker run -p 8501:8501 ai-banking-insights
```
### Environment Variables
- `JWT_SECRET` – secret key (override default in production).
- `DATABASE_PATH` – path to SQLite DB (default `database/banking.db`).

---

## 📚 Documentation
- **High‑level architecture diagram** – see `assets/architecture.png` (or the embedded ER diagram below).
- **ER Diagram** – visualises tables and relationships.

![ER Diagram](file:///C:/Users/Nylup/.gemini/antigravity-ide/brain/30905392-0015-4ebe-baf8-1b7066c1c6fe/er_diagram_1784485795522.png)

---

## 🛡️ Security Considerations
- Passwords stored using BCrypt.
- JWT tokens signed with HS256; 24‑hour expiry.
- All user inputs are validated; CSV uploads undergo strict schema checks.
- Audit logs retain records even if a user is deleted.

---

## 📈 Roadmap & Future Work
- **CI/CD** – GitHub Actions for linting, tests, and Docker image publishing.
- **Automated unit tests** – pytest coverage for utils and model pipelines.
- **Live data streaming** – Kafka/WebSocket integration for real‑time transaction feeds.
- **Advanced visualisations** – Dash or React front‑end for richer UI.
- **Multi‑tenant support** – Separate schemas per bank.
- **Performance** – Query caching, async DB access.

---

## 🤝 License
This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

## ✉️ Contact & Support
- **Author**: Nagaraj P.
- **GitHub**: https://github.com/nagarajp2106
- **Issue Tracker**: Use the GitHub Issues tab for bugs, feature requests, or questions.
