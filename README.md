# AI-Powered Retail Banking Customer Insights Platform

A full-stack, AI-powered retail banking analytics platform built with Streamlit, SQLite, and Python. The platform enables banks to manage customer profiles, analyze transaction and loan trends, predict churn, estimate customer lifetime value, recommend products, and automatically generate data-driven business insights.

🌐 **GitHub Repository**: [nagarajp2106/CIP](https://github.com/nagarajp2106/CIP)

---

## 🚀 Key Features

* **Role-Based Authentication**: Secure JWT-based authentication supporting 3 roles (Admin, Manager, Analyst).
* **Interactive Dashboards**: Real-time KPI metrics and 8+ Plotly visualizations covering customer demographics, regional distributions, monthly transactions, and loan portfolios.
* **Robust Data Pipeline**: Data validation checks, auto-cleaning (duplicate removal, missing value imputation), and feature engineering (value scores, utilization ratios, age/income categories).
* **6 Core Customer Insights Modules**:
  * **Customer Segmentation**: KMeans Clustering with 2D/3D PCA projections.
  * **Churn Prediction**: Random Forest Classifier for stay vs. leave probabilities.
  * **CLV Prediction**: Gradient Boosting Regressor tracking tier levels (Platinum, Gold, Silver, Bronze).
  * **Product Recommendation**: Dual rule-based and collaborative similarity matcher.
  * **Deposit Subscription Prediction**: Random Forest Classifier mapping prospective targeting campaigns.
  * **AI Business Insights Engine**: 15+ automated data-driven insights scanning correlations in risk, customer tenure, branch performance, and deposit volumes.
* **Professional Report Export**: Generate custom executive, transaction, and segmentation reports in Excel (`.xlsx` formatted) and PDF (`ReportLab` styled) formats.
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
│   ├── clv.pkl                     # Gradient Boosting Regressor
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
└── pages/                          # Role-gated functional modules (17 pages)
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
    ├── 13_CLV_Prediction.py
    ├── 15_Product_Recommendation.py
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
| `manager` | `manager123` | **Manager** | Executive dashboards, analytics, ML predictions, reports, insights |
| `analyst` | `analyst123` | **Analyst** | CSV upload, cleaning panel, EDA, segmentation, reports |

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
Train all 4 regression, classification, and clustering models:
```bash
python -c "from utils.prediction import train_all_models; train_all_models()"
```

### 5. Launch the Web App
Run the Streamlit application:
```bash
streamlit run app.py
```

The application will launch in your default web browser at `http://localhost:8501`.
