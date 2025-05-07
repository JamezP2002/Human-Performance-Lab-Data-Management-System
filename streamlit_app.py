import streamlit as st
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt

# the menu pages
vo2Max_impl = st.Page("VO2Max_impl.py", title="Upload Data")
home = st.Page("home.py", title="Home")
report_creator_page = st.Page("report_creator_page.py", title="Create Report")
data_viewer = st.Page("report_viewer_page.py", title="View Report")

# Setup MongoDB connection
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
load_dotenv(dotenv_path)
database_credentials = os.getenv("database_credentials")

client = MongoClient(database_credentials)
db = client['performance-lab']
auth_users_col = db['authUsers']

# Setup session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

st.set_page_config(page_title="CHAMP HPL SCSU", page_icon=":material/edit:", layout="wide", initial_sidebar_state="expanded")

# =====================
# LOGIN SECTION
# =====================
if not st.session_state.logged_in:
    # Hide the sidebar when logged out
    hide_sidebar_style = """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
    """
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>🔒 Login Required</h1>", unsafe_allow_html=True)

    # Create a centered container
    with st.container():
        # Use columns to center the expander
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            with st.expander("Click to Log In", expanded=True):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")

                if st.button("Log In"):
                    user = auth_users_col.find_one({"username": username})

                    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success(f"✅ Welcome, {username}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password.")

else:
    # =====================
    # MAIN APP NAVIGATION
    # =====================
    st.sidebar.success(f"Logged in as {st.session_state.username}")

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("Logged out successfully.")
        st.rerun()

    # Now show the normal app!
    pg = st.navigation(
        {
            "🏠 HOMEPAGE": [home], 
            "📂 UPLOADER": [vo2Max_impl],
            "📑 REPORTS": [report_creator_page, data_viewer]
        }
    )
    pg.run()
