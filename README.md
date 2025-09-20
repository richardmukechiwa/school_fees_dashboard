# school_fees_dashboard

# School Fees Dashboard

A **Streamlit-based dashboard** for school administrators to track and manage student fee payments. Connects to **Airtable** for data storage and supports **dynamic KPI thresholds**, color-coded status indicators, and CSV exports.

---

## Features

- **Secure Login:** Admin login with hashed passwords.
- **KPI Threshold Settings:** Configure high outstanding alerts and % collected thresholds.
- **Dashboard Metrics:**
  - Total Outstanding Fees
  - Parents Owing
  - % Collected (color-coded: green, orange, red)
- **Outstanding by Parent:** Bar charts and summary tables.
- **Detailed Fee Records:** View full fee history with color-coded `Status` and `Balance Due`.
- **Update Payments:** Record new payments for students without touching computed fields.
- **Download Reports:** Export All Fees or Unpaid Fees as CSV.
- **Theme Toggle:** Light and Dark mode support.

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/school-fees-dashboard.git
cd school-fees-dashboard

Install Dependencies

pip install -r requirements.txt

Configure Environment Variables

API_KEY=your_airtable_api_key
BASE_ID=your_airtable_base_id
SCHOOLS_TABLE=Schools
FEES_TABLE=Fees

Run the Dashboard

streamlit run app.py

Usage Guide
Login

Enter your school admin email and password.

Optionally check Remember me.

Click Login to access the dashboard.

KPI Threshold Settings

Expand ⚙️ KPI Threshold Settings.

Set High Outstanding Alert (USD) to trigger warnings.

Set % Collected Green Threshold and % Collected Orange Threshold.

Close the section to view metrics.

Dashboard Metrics

Total Outstanding: Sum of unpaid balances.

Parents Owing: Count of parents with unpaid fees.

% Collected: Shows fee collection progress with color-coded delta.

Outstanding by Parent: Expand to see bar charts and parent summaries.

Detailed Fees Records: Expand to see all fee records with color-coded Status and Balance Due.

Update Payment

Expand Update Payment.

Select Parent → Child → Enter Amount Paid.

Click Submit Payment.

Dashboard updates local balances and status automatically.

Download Reports

Expand Download Reports to export CSVs:

All Fees CSV

Unpaid Fees CSV

Theme Toggle

Switch between Light and Dark modes via the sidebar.

Notes

balance_due is a computed field in Airtable; the dashboard updates only amount_paid to avoid errors.

Color-coded KPI thresholds:

Green: % collected above green threshold

Orange: % collected between orange and green

Red: % collected below orange threshold
