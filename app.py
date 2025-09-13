import streamlit as st
import bcrypt
from pyairtable import Table

# get .env variables
from dotenv import load_dotenv  
import os
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_ID = os.getenv("BASE_ID")     
SCHOOLS_TABLE = os.getenv("SCHOOLS_TABLE")





# Airtable setup
#API_KEY = "your_airtable_api_key"
#BASE_ID = "your_base_id"
#SCHOOLS_TABLE = "Schools"

schools_table = Table(API_KEY, BASE_ID, SCHOOLS_TABLE)

# Password helpers
def hash_password(password: str) -> str:
    """Hash a password with bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(password: str, hashed: str) -> bool:
    """Verify password against stored bcrypt hash"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# Login function
def login_school():
    st.title("School Login")

    email = st.text_input("Admin Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            # Query Airtable for this email
            records = schools_table.all(formula=f"{{admin_email}} = '{email}'")
            if not records:
                st.error("School not found")
                return None

            school = records[0]["fields"]
            stored_hash = school.get("admin_password")

            if stored_hash and check_password(password, stored_hash):
                st.success(f"Welcome {school['school_name']}!")
                return school
            else:
                st.error("Invalid password")
                return None
        except Exception as e:
            st.error(f"Error: {e}")
            return None

# Example: protect dashboard
school = login_school()
if school:
    st.write(f"This is the dashboard for {school['school_name']}")
