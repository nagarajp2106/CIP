# Project Inventory Report

This report summarizes the projects developed and completed in the workspace `c:\Users\Nylup\Desktop\CIP` based on the conversation history and codebase analysis.

---

## 📊 Project Inventory

| Project Name | Objective | Primary Technologies | Status | Modules / Foldes | Key Milestone |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AI-Powered Retail Banking Customer Insights Platform** | Secure, role-based analytics platform for customer churn, risk, segment profiling, fraud detection, and reporting. | Python, Streamlit, SQLite, Scikit-learn, XGBoost, Plotly | **Completed** | `app.py`, `authentication.py`, `utils/`, `pages/`, `assets/` | End-to-end integration of 8 predictive models, custom light theme UX styling, and remote synchronization to GitHub. |

---

## 🔍 Detailed Project Profiles

### 1. AI-Powered Retail Banking Customer Insights Platform

#### 📋 Purpose & Objective
To build a premium, full-stack, AI-powered banking dashboard for bank relationship managers, loan officers, auditors, data analysts, and executive managers to monitor client activity, assess risk, predict future behaviors (churn, loan default, product subscriptions), and export administrative summaries.

#### 🛠️ Technologies & Frameworks Used
* **UI/UX Layer**: Streamlit, HTML5, custom Vanilla CSS (`assets/style.css`), Streamlit Config Engine (`.streamlit/config.toml`).
* **Database Layer**: SQLite3 (`database.py`, `utils/database_utils.py`), Pandas, NumPy.
* **Security & Auth**: PyJWT, Bcrypt (`authentication.py`, `jwt_handler.py`, `utils/auth.py`).
* **AI & Machine Learning**: Scikit-Learn, XGBoost, Joblib (`utils/prediction.py`).
* **Reports Compilation**: OpenPyXL, ReportLab (`utils/reports.py`).
* **Analytics & Visualization**: Plotly, Plotly Graph Objects (`utils/visualization.py`).

#### ✨ Key Features Implemented
1. **Role-Based Authentication**: Secure JWT session verification supporting 6 specific roles:
   * **Admin**: Complete CRUD database panel and system backup capabilities.
   * **Bank Manager**: Executive summaries, Plotly charts, and business insights.
   * **Relationship Manager**: Customer segment profiles, churn predictions, and product recommendation maps.
   * **Loan Officer**: Portfolio metrics, credit risk assessment, and loan approvals.
   * **Data Analyst**: Dataset upload parser, data quality panel, and interactive EDA.
   * **Auditor**: Read-only activity audits, transaction logs, and fraud timelines.
2. **Unified Navigation Sidebar**: An automated shared sidebar layout displaying logged-in credentials, user-specific role badges, and an immediate session logout button.
3. **Responsive Spacing Grid**: CSS breakpoints targeting different monitor viewports (desktop, laptop, mobile) to avoid component stretching and keep data tables and metrics cleanly aligned.
4. **9 Predictive/Analytical Modules**:
   * *Customer Segmentation*: KMeans Clustering (k=5) with 2D/3D PCA projection charts.
   * *Churn Prediction*: Random Forest Classifier (Stay vs. Leave probabilities).
   * *Credit Risk*: XGBoost Classifier (Low, Medium, High risk indicators).
   * *Loan Approval*: Random Forest Classifier with explicit decision factors explanations.
   * *CLV Prediction*: Gradient Boosting Regressor tracking tier levels (Platinum, Gold, Silver, Bronze).
   * *Fraud Detection*: Isolation Forest anomaly tracker with risk heatmaps.
   * *Product Recommendation*: Dual rule-based and collaborative similarity matcher.
   * *Income Prediction*: Gradient Boosting Regressor with error distribution metrics.
   * *Deposit Subscription*: Random Forest Classifier mapping prospective targeting campaigns.
5. **Business Insights Engine**: 15+ automated data-driven insights scanning correlations in risk, customer tenure, branch performance, and deposit volumes.
6. **Excel & PDF Exporters**: Multi-sheet formatted workbooks and custom PDF styling for 8 specific types of records.

#### 📈 Major Milestones Achieved
* **Milestone 1**: Created modular database backend seeding 5,000 customers, 8,000 accounts, and 50,000 transaction events out of the box.
* **Milestone 2**: Created full secure token validation pipeline and custom theme stylesheets.
* **Milestone 3**: Completed coding for 21 standalone pages, each containing role-based security checks.
* **Milestone 4**: Fully trained, evaluated, and compiled 8 distinct machine learning models.
* **Milestone 5**: Verified all functional parts via automated tests and successfully synchronized to GitHub at `https://github.com/nagarajp2106/CIP`.

#### ⚠️ Pending Tasks or Known Issues
* None. All elements are fully developed, tested, and passing integration checks.
