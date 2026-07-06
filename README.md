# AI-Powered Retail Banking Customer Insights Platform

A full-stack, AI-powered retail banking analytics platform built with Streamlit, SQLite, and Python. The platform enables banks to manage customer profiles, analyze transaction and loan trends, assess credit risks, predict churn, detect fraud, and automatically generate data-driven business insights.

🌐 **GitHub Repository**: [nagarajp2106/CIP](https://github.com/nagarajp2106/CIP)

---

## 🚀 Key Features

* **Role-Based Authentication**: Secure JWT-based authentication supporting 6 unique roles (Admin, Bank Manager, Relationship Manager, Loan Officer, Data Analyst, Auditor).
* **Interactive Dashboards**: Real-time KPI metrics and 8+ Plotly visualizations covering customer demographics, regional distributions, monthly transactions, and loan portfolios.
* **Robust Data Pipeline**: Data validation checks, auto-cleaning (duplicate removal, missing value imputation), and feature engineering (value scores, utilization ratios, age/income categories).
* **9 Predictive ML Modules**: Fully integrated analytical models for churn, credit risk (XGBoost), loan approval, customer lifetime value, fraud detection (Isolation Forest), product recommendations, and campaign targeting.
* **AI Business Insights**: Dynamic generation of 15+ actionable, data-driven insights across risk, operations, and revenue.
* **Professional Report Export**: Generate custom executive, transaction, and fraud reports in Excel (`.xlsx` formatted) and PDF (`ReportLab` styled) formats.
* **Light Theme UI/UX**: Premium, high-contrast light theme with fully responsive desktop spacing and a persistent shared sidebar.

---

## 🛠️ Technology Stack

* **Front-End & Application**: Streamlit, Custom CSS
* **Database**: SQLite3
* **Data Processing**: Pandas, NumPy
* **Machine Learning**: Scikit-Learn, XGBoost, Joblib
* **Security & Auth**: PyJWT, Bcrypt
* **Report Generation**: OpenPyXL, ReportLab
* **Visualization**: Plotly, Graph Objects

---

## 📁 Folder Structure

```
AI_Banking_Customer_Insights/
├── app.py                          # Main Streamlit application entrypoint
├── authentication.py               # Auth modules & unified sidebar renderer
├── config.py                       # Configuration & theme colors
├── database.py                     # SQLite schema & synthetic data generator
├── jwt_handler.py                  # JWT lifecycle management
├── requirements.txt                # Pinned dependencies
├── .gitignore                      # Git exclusion rules
│
├── assets/
│   └── style.css                   # Custom Light theme CSS overrides
│
├── database/
│   └── banking.db                  # SQLite database (auto-generated)
│
├── datasets/
│   └── bank_customers.csv          # Sample dataset export (1000 records)
│
├── models/                         # Trained ML model pickles (auto-generated)
│   ├── segmentation.pkl            # KMeans Clustering
│   ├── churn.pkl                   # Random Forest Classifier
│   ├── credit_risk.pkl             # XGBoost Classifier
│   ├── loan.pkl                    # Random Forest Classifier
│   ├── clv.pkl                     # Gradient Boosting Regressor
│   ├── fraud.pkl                   # Isolation Forest Anomaly detector
│   ├── income.pkl                  # Gradient Boosting Regressor
│   └── deposit.pkl                 # Random Forest Classifier
│
├── utils/                          # Reusable modules & controllers
│   ├── __init__.py
│   ├── auth.py                     # User CRUD & Bcrypt password utility
│   ├── database_utils.py           # SQL paginator & backup tools
│   ├── feature_engineering.py      # Category builders & tenure calculators
│   ├── prediction.py               # ML training & evaluation functions
│   ├── preprocessing.py            # Upload validator & anomaly detector
│   ├── recommendation.py           # Rules & similarity-based recommender
│   ├── reports.py                  # Excel/PDF layout compilers
│   └── visualization.py            # Plotly builders & metric card HTML
│
└── pages/                          # Role-gated functional modules (21 pages)
    ├── 1_Dashboard.py
    ├── 2_Data_Upload.py
    ├── 3_Data_Preprocessing.py
    ├── 4_Database_Manager.py
    ├── 5_Customer_Management.py
    ├── 6_Transaction_Analytics.py
    ├── 7_Loan_Analytics.py
    ├── 8_EDA.py
    ├── 9_Customer_Segmentation.py
    ├── 10_Churn_Prediction.py
    ├── 11_Credit_Risk.py
    ├── 12_Loan_Approval.py
    ├── 13_CLV_Prediction.py
    ├── 14_Fraud_Detection.py
    ├── 15_Product_Recommendation.py
    ├── 16_Income_Prediction.py
    ├── 17_Deposit_Prediction.py
    ├── 18_AI_Business_Insights.py
    ├── 19_Reports.py
    ├── 20_Admin.py
    └── 21_Settings.py
```

---

## 🔑 Demo Access Credentials

The platform features role-based access control. Log in using one of the predefined demo accounts:

| Username | Password | Role | Features Gated |
|:---|:---|:---|:---|
| `admin` | `admin123` | **Admin** | Full system configuration, backup, user CRUD, page management |
| `manager` | `manager123` | **Bank Manager** | Executive dashboards, analytical charts, reports, insights |
| `relationship` | `relation123` | **Relationship Manager** | Profiles, history, churn risk, product recommendations |
| `loanofficer` | `loan123` | **Loan Officer** | Loan analytics, risk scoring, approval predictions |
| `analyst` | `analyst123` | **Data Analyst** | CSV upload, cleaning panel, feature scaling, interactive EDA |
| `auditor` | `auditor123` | **Auditor** | Read-only access to transaction activity & fraud timelines |

---

## ⚙️ Installation & Setup

Follow these steps to run the application on your local machine:

### 1. Clone the Repository
```bash
git clone https://github.com/nagarajp2106/CIP.git
cd CIP
```

### 2. Install Dependencies
Make sure you have Python installed, then install all requirements:
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
Seed 5,000 realistic synthetic customers, transactions, loans, cards, and default users:
```bash
python -c "from database import init_db, seed_demo_data; init_db(); seed_demo_data(); print('Database seeded successfully!')"
```

### 4. Train Machine Learning Models
Train all 8 regression, classification, and anomaly detection models:
```bash
python -c "from utils.prediction import train_all_models; train_all_models()"
```

### 5. Launch the Web App
Run the Streamlit application:
```bash
streamlit run app.py
```

The application will launch in your default web browser at `http://localhost:8501`.
