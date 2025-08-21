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

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Login/Logout functionality
if not st.session_state.logged_in:
    
    st.title("🔒 Login Please")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        user = auth_users_col.find_one({"username": username})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

else:
    st.sidebar.success(f"✅ Logged in as {st.session_state.username}")

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("Logged out successfully.")
        st.rerun()

    st.title("🏠 Home")
    st.write(f"Hello, **{st.session_state.username}**! You are now logged in.")
