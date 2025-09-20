import os
import bcrypt
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_ID = os.getenv("BASE_ID")
SCHOOLS_TABLE = os.getenv("SCHOOLS_TABLE")

# Initialize Airtable API
api = Api(API_KEY)
schools_table = api.table(BASE_ID, SCHOOLS_TABLE)

# Password helper
def hash_password(password: str) -> str:
    """Hash a password and return a string for Airtable"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Define the schools and new password
school_ids = ["S001", "S002", "S003", "S004"]  # replace with your actual school_ids
new_password = "password123"  # one-time password for all schools
hashed_pw = hash_password(new_password)

# Loop through each school and update password
for sid in school_ids:
    # Find the record by school_id
    records = schools_table.all(formula=f"{{school_id}} = '{sid}'")
    
    if not records:
        print(f"No record found for school_id: {sid}")
        continue

    record_id = records[0]["id"]
    
    # Update the password field with the hashed password
    try:
        updated = schools_table.update(record_id, {"admin_password": hashed_pw})
        print(f"Updated school {sid} successfully. Hashed password stored.")
    except Exception as e:
        print(f"Failed to update school {sid}: {e}")

print("One-time setup complete. All specified schools have updated passwords.")

# Note: After this one-time setup, ensure to change passwords to unique ones for each school
