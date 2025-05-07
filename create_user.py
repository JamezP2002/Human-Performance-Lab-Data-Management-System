import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import bcrypt

# Load environment variables
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
load_dotenv(dotenv_path)
database_credentials = os.getenv("database_credentials")

# Connect to MongoDB
client = MongoClient(database_credentials)
db = client['performance-lab']
auth_users_col = db['authUsers']

st.title("🛠️ Create New User Account")

username = st.text_input("Enter Username")
password = st.text_input("Enter Password", type="password")

if st.button("Create Account"):
    if not username or not password:
        st.error("Username and password cannot be empty.")
    else:
        # Check if user already exists
        existing_user = auth_users_col.find_one({"username": username})
        if existing_user:
            st.error("Username already exists. Try a different one.")
        else:
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Insert into MongoDB
            auth_users_col.insert_one({
                "username": username,
                "password": hashed_password,
            })

            st.success(f"✅ Account created successfully for {username}")