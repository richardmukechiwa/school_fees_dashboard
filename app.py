import streamlit as st
import pandas as pd
from pyairtable import Table

# Airtable API setup
API_KEY = "your_airtable_api_key"
BASE_ID = "your_base_id"
TABLE_NAME = "School_Parents"

table = Table(API_KEY, BASE_ID, TABLE_NAME)

# Fetch records
records = table.all()
data = []
for r in records:
    f = r['fields']
    due = float(f.get("Due Amount", 0) or 0)
    paid = float(f.get("Amount Paid", 0) or 0)
    balance = due - paid
    
    # Derive status
    if paid == 0:
        status = "unpaid"
    elif paid < due:
        status = "partial"
    else:
        status = "paid"
    
    data.append({
        "Record ID": r['id'],
        "Parent ID": f.get("Parent ID", ""),
        "Parent": f.get("Parent Name", ""),
        "Child": f.get("Student Name", ""),
        "Due Amount": due,
        "Amount Paid": paid,
        "Balance Due": balance,
        "Due Date": f.get("Due Date", ""),
        "Status": status
    })

df = pd.DataFrame(data)

# Filter only unpaid balances
df_unpaid = df[df["Balance Due"] > 0]

st.title("School Fees Reminder Dashboard")
st.dataframe(df_unpaid)

# Parent-level aggregation
parent_summary = (
    df_unpaid.groupby(["Parent ID", "Parent"], as_index=False)[["Balance Due"]]
    .sum()
)
st.subheader("Outstanding by Parent")
st.dataframe(parent_summary)

st.metric("Total Outstanding", f"USD {df_unpaid['Balance Due'].sum():,.2f}")

# ---- Payment Update Section ----
st.subheader("Update Payment")

parent_choice = st.selectbox("Select Parent", parent_summary["Parent"])
child_choice = st.selectbox("Select Child", df[df["Parent"] == parent_choice]["Child"])
amount = st.number_input("Enter Amount Paid", min_value=0.0)

if st.button("Submit Payment"):
    record = df[
        (df["Parent"] == parent_choice) & (df["Child"] == child_choice)
    ].iloc[0]

    record_id = record["Record ID"]
    current_paid = record["Amount Paid"]
    due = record["Due Amount"]

    new_paid = current_paid + amount
    new_balance = due - new_paid
    
    # New status logic
    if new_paid == 0:
        new_status = "unpaid"
    elif new_paid < due:
        new_status = "partial"
    else:
        new_status = "paid"

    # Push updates back to Airtable
    table.update(record_id, {
        "Amount Paid": new_paid,
        "Balance Due": new_balance,
        "Status": new_status
    })

    st.success(
        f"Updated {child_choice}: Paid = USD {new_paid:,.2f}, "
        f"Balance = USD {new_balance:,.2f}, Status = {new_status}"
    )
