import streamlit as st
import pandas as pd
from pyairtable import Api
import bcrypt
import os
import time
from dotenv import load_dotenv
import plotly.express as px

# ---- Load environment variables ----
# Locally: from .env
# On Streamlit Cloud: from st.secrets
if os.path.exists(".env"):
    load_dotenv()

def get_secret(key, default=None):
    """Fetch variable from st.secrets (Cloud) or os.getenv (.env)"""
    if key in st.secrets:
        source = "st.secrets"
        val = st.secrets[key]
    else:
        source = ".env"
        val = os.getenv(key, default)

    if val is None:
        raise ValueError(f"{key} is not set in {source}. Please configure it.")
    return str(val).strip().strip('"').strip("'")

# ---- Airtable Config ----
API_KEY = get_secret("API_KEY")
BASE_ID = get_secret("BASE_ID")
SCHOOLS_TABLE = get_secret("SCHOOLS_TABLE")
FEES_TABLE = get_secret("FEES_TABLE", "Fees")

st.sidebar.info(f"✅ Config loaded from {'st.secrets' if 'API_KEY' in st.secrets else '.env'}")

# ---- Airtable Setup ----
try:
    api = Api(API_KEY)
    schools_table = api.table(BASE_ID, SCHOOLS_TABLE)
    fees_table = api.table(BASE_ID, FEES_TABLE)
except Exception as e:
    st.error(f"Failed to connect to Airtable: {e}")
    st.stop()


# ---- Page Setup ----
st.set_page_config(page_title="School Fees Dashboard", layout="wide")

# ---- Theme Toggle ----
theme_choice = st.sidebar.radio("Theme Mode", ["Light", "Dark"])
if theme_choice == "Dark":
    st.markdown("""
        <style>
        .reportview-container {background-color: #0E1117; color: #ffffff;}
        .stButton>button {background-color: #1f2937; color: #ffffff;}
        .stSelectbox>div>div>div {background-color: #1f2937; color: #ffffff;}
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .reportview-container {background-color: #f9f9f9; color: #000000;}
        </style>
    """, unsafe_allow_html=True)

# ---- Password Helper ----
def check_password(password: str, hashed_str: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_str.encode("utf-8"))

# ---- Login & Session Management ----
SESSION_TIMEOUT = 1800  # 30 minutes

def login(email: str, password: str) -> bool:
    try:
        records = schools_table.all(formula=f"{{admin_email}} = '{email}'")
        if not records:
            return False
        school = records[0].get("fields", {})
        stored_hash = school.get("admin_password")
        if stored_hash and check_password(password, stored_hash):
            st.session_state['school_id'] = school.get("school_id")
            st.session_state['school_name'] = school.get("school_name")
            st.session_state['login_time'] = time.time()
            st.session_state['logged_in'] = True
            return True
        return False
    except Exception as e:
        st.error(f"Login error: {e}")
        return False

def logout():
    for key in ["school_id", "school_name", "login_time", "logged_in"]:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.rerun()

# ---- Normalizer ----
def normalize_text(value):
    if isinstance(value, list):
        return ", ".join([str(v).strip() for v in value if v])
    if isinstance(value, str):
        return value.strip()
    return str(value or "").strip()

# ---- Parse Amount Helper ----
def parse_amount(val):
    if isinstance(val, str):
        return float(val.replace("$", "").replace(",", "").strip())
    try:
        return float(val)
    except:
        return 0.0

# ---- Fetch & Normalize Fees Data ----
@st.cache_data(ttl=300)
def fetch_school_fees(school_id: str) -> pd.DataFrame:
    records = fees_table.all(formula=f'{{school_id}}="{school_id}"')
    data = []
    for r in records:
        f = r.get("fields", {})
        due = parse_amount(f.get("due_amount"))
        paid = parse_amount(f.get("amount_paid"))
        balance = parse_amount(f.get("balance_due")) or (due - paid)

        parent_name = normalize_text(f.get("Parent Name")).title()
        parent_whatsapp = normalize_text(f.get("Parent WhatsApp"))
        parent_email = normalize_text(f.get("Parent Email")).lower()

        # Normalize student_name
        raw_student = f.get("student_name", "")
        if isinstance(raw_student, list):
            student_list = [normalize_text(x).title() for x in raw_student if normalize_text(x)]
        elif isinstance(raw_student, str):
            student_list = [s.strip().title() for s in raw_student.split(",") if s.strip()]
        else:
            student_list = []
        student_display = ", ".join(student_list)

        status = (f.get("status") or "").strip().lower()
        if not status:
            status = "unpaid" if paid == 0 else ("partial" if paid < due else "paid")

        data.append({
            "Record ID": r.get('id', ""),
            "Fee ID": f.get("fee_id", ""),
            "School ID": f.get("school_id", ""),
            "School": normalize_text(f.get("school_name")).title(),
            "Parent Name": parent_name,
            "Parent WhatsApp": parent_whatsapp,
            "Parent Email": parent_email,
            "student_id": f.get("student_id", ""),
            "student_name": student_list,
            "student_display": student_display,
            "Due Amount": due,
            "Amount Paid": paid,
            "Balance Due": balance,
            "Status": status,
            "Reminder Type": f.get("reminder_type", ""),
            "Escalated": f.get("escalated", False),
            "Last Reminder": f.get("last_reminder_date", "")
        })
    return pd.DataFrame(data)

# ---- Color Helpers ----
def color_status(val):
    if val == "unpaid":
        return "background-color: #ff4c4c" if theme_choice == "Dark" else "background-color: #ffcccc"
    elif val == "partial":
        return "background-color: #ffdb4c" if theme_choice == "Dark" else "background-color: #fff2cc"
    elif val == "paid":
        return "background-color: #4caf50" if theme_choice == "Dark" else "background-color: #ccffcc"
    return ""

def color_balance(val):
    if val > 0:
        return "color: #ff6b6b; font-weight: bold" if theme_choice == "Dark" else "color: red; font-weight: bold"
    return ""

# ---- Dashboard ----
def show_dashboard():
    elapsed = time.time() - st.session_state.get('login_time', 0)
    if elapsed > SESSION_TIMEOUT:
        st.warning("Session expired. Please log in again.")
        logout()

    # ---- KPI Threshold Settings ----
    with st.expander("⚙️ KPI Threshold Settings", expanded=False):
        st.session_state.setdefault("high_outstanding_threshold", 1000.0)
        st.session_state.setdefault("percent_collected_green", 80)
        st.session_state.setdefault("percent_collected_orange", 50)

        st.session_state["high_outstanding_threshold"] = st.number_input(
            "High Outstanding Alert (USD)",
            min_value=0.0,
            value=st.session_state["high_outstanding_threshold"]
        )
        st.session_state["percent_collected_green"] = st.slider(
            "% Collected Green Threshold", 0, 100,
            st.session_state["percent_collected_green"]
        )
        st.session_state["percent_collected_orange"] = st.slider(
            "% Collected Orange Threshold", 0, 100,
            st.session_state["percent_collected_orange"]
        )

    # ---- Fetch Data ----
    df = fetch_school_fees(st.session_state['school_id'])
    df_unpaid = df[df["Balance Due"] > 0]

    st.title(f"📊 Fees Dashboard - {st.session_state['school_name']}")

    total_outstanding = df_unpaid["Balance Due"].sum()
    num_parents = df_unpaid["Parent Name"].nunique()
    total_due = df["Due Amount"].sum()
    percent_collected = 100 * (total_due - total_outstanding) / total_due if total_due > 0 else 0

    # ---- KPI Color Helpers ----
    def get_percent_collected_color(percent_collected):
        if percent_collected >= st.session_state["percent_collected_green"]:
            return "green"
        elif percent_collected >= st.session_state["percent_collected_orange"]:
            return "orange"
        else:
            return "red"

    def get_outstanding_color(total_outstanding):
        if total_outstanding <= st.session_state["high_outstanding_threshold"] * 0.5:
            return "green"
        elif total_outstanding <= st.session_state["high_outstanding_threshold"]:
            return "orange"
        else:
            return "red"

    # ---- KPI Display ----
    col1, col2, col3 = st.columns(3)
    outstanding_color = get_outstanding_color(total_outstanding)
    if outstanding_color == "green":
        col1.success(f"💵 Total Outstanding: USD {total_outstanding:,.2f} (Below threshold)")
    elif outstanding_color == "orange":
        col1.warning(f"⚠️ Total Outstanding: USD {total_outstanding:,.2f} (Approaching threshold)")
    else:
        col1.error(f"🚨 Total Outstanding: USD {total_outstanding:,.2f} (Exceeded threshold)")

    col2.metric("👨‍👩‍👦 Parents Owing", num_parents)

    pct_color = get_percent_collected_color(percent_collected)
    color_map = {"green": "#4caf50", "orange": "#ff9800", "red": "#f44336"}
    col3.markdown(f"<h3 style='color:{color_map[pct_color]}'>📈 % Collected: {percent_collected:.1f}%</h3>", unsafe_allow_html=True)

    # ---- Outstanding by Parent ----
    with st.expander("Outstanding by Parent"):
        if not df_unpaid.empty:
            parent_summary = (
                df_unpaid.groupby(
                    ["Parent Name", "Parent WhatsApp", "Parent Email"], as_index=False
                )[["Balance Due"]].sum().sort_values("Balance Due", ascending=False)
            )

            def parent_balance_color(balance):
                if balance <= st.session_state["high_outstanding_threshold"] * 0.5:
                    return "green"
                elif balance <= st.session_state["high_outstanding_threshold"]:
                    return "orange"
                else:
                    return "red"

            parent_summary["Color"] = parent_summary["Balance Due"].apply(parent_balance_color)

            fig = px.bar(
                parent_summary,
                x="Parent Name",
                y="Balance Due",
                color="Color",
                color_discrete_map={"green":"#4caf50","orange":"#ff9800","red":"#f44336"},
                text="Balance Due"
            )
            fig.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
            fig.update_layout(yaxis_title="Balance Due (USD)", xaxis_title="Parent", showlegend=False, margin=dict(t=30,b=20))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(parent_summary.drop(columns="Color"))
        else:
            st.info("No outstanding fees for this school.")

    # ---- Detailed Fees Records ----
    with st.expander("Detailed Fees Records"):
        st.dataframe(df.style.map(color_status, subset=["Status"]).map(color_balance, subset=["Balance Due"]))

    # ---- Download Reports ----
    with st.expander("Download Reports"):
        st.download_button("Download All Fees CSV", df.to_csv(index=False).encode('utf-8'),
                           file_name=f"{st.session_state['school_name']}_all_fees.csv", mime="text/csv")
        st.download_button("Download Unpaid Fees CSV", df_unpaid.to_csv(index=False).encode('utf-8'),
                           file_name=f"{st.session_state['school_name']}_unpaid_fees.csv", mime="text/csv")

    # ---- Update Payment Section ----
    with st.expander("Update Payment"):
        parent_choice = st.selectbox("Select Parent", df_unpaid["Parent Name"].unique())
        parent_records = df[df["Parent Name"] == parent_choice]

        student_options = []
        for s in parent_records["student_name"]:
            if isinstance(s, list):
                student_options.extend(s)
            elif isinstance(s, str):
                student_options.append(normalize_text(s).title())
        student_options = sorted(set(student_options))

        if student_options:
            child_choice = st.selectbox("Select Child", student_options)
            amount = st.number_input("Enter Amount Paid", min_value=0.0)

            if st.button("Submit Payment"):
                found = False
                for _, rec in parent_records.iterrows():
                    if child_choice in rec["student_name"]:
                        record_id = rec["Record ID"]
                        current_paid = rec["Amount Paid"]
                        due = rec["Due Amount"]
                        new_paid = current_paid + amount
                        new_status = "unpaid" if new_paid == 0 else ("partial" if new_paid < due else "paid")

                        # Update only writable fields
                        fees_table.update(record_id, {
                            "amount_paid": new_paid
                        })

                        st.success(f"Updated {child_choice}: Paid = USD {new_paid:,.2f}, Status = {new_status}")
                        found = True
                        break
                if not found:
                    st.error(f"No record found for {child_choice} under {parent_choice}.")

    # ---- Logout Button ----
    st.markdown("""
        <style>.logout-btn {position: fixed; bottom: 20px; right: 20px; z-index: 9999;}</style>
    """, unsafe_allow_html=True)
    if st.button("Logout", key="sticky_logout"):
        logout()

# ---- Main ----
def main():
    params = st.query_params
    if params.get("remember") == ["1"]:
        if not st.session_state.get("logged_in", False) and "school_id" in st.session_state:
            st.session_state['logged_in'] = True

    if st.session_state.get('logged_in', False):
        show_dashboard()
    else:
        st.title("School Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me")
        if st.button("Login"):
            if login(email, password):
                st.success(f"Welcome {st.session_state['school_name']}")
                if remember_me:
                    st.query_params.update({"remember": "1"})
                st.rerun()
            else:
                st.error("Invalid credentials")

if __name__ == "__main__":
    main()


