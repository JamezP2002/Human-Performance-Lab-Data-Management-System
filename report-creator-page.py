from pymongo import MongoClient
import streamlit as st
import os
from dotenv import load_dotenv
import boto3
from vo2max_test import VO2MaxTest

# find and load the .env file
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
load_dotenv(dotenv_path)

# load the environment variables
database_credentials = os.getenv("database_credentials")
aws_access_key_id = os.getenv("aws_access_key_id")
aws_secret_access_key = os.getenv("aws_secret_access_key")

# connecting to s3 bucket
s3_client = boto3.client('s3',
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key,
                          region_name='us-east-1'
                          )

# connecting to mongodb
client = MongoClient(database_credentials)
db = client['performance-lab']

# Session state management for test types
if 'test_section' not in st.session_state:
    st.session_state.test_section = True
if 'vo2max_test' not in st.session_state:
    st.session_state.vo2max_test = False
if 'rmr_test' not in st.session_state:
    st.session_state.rmr_test = False

# Navigation logic
def go_to_vo2max():
    st.session_state.test_section = False
    st.session_state.vo2max_test = True
    st.session_state.rmr_test = False

def go_to_rmr():
    st.session_state.test_section = False
    st.session_state.vo2max_test = False
    st.session_state.rmr_test = True

if st.session_state.test_section:

    # App Title
    st.title("Report Creation and PDF Generation")
    st.write("Champ Human Performance Lab")

    # Get available collections and insert "None"
    available_collections = db.list_collection_names()
    test_options = ["None"] + available_collections

    selected_test = st.selectbox("Select Test Type", test_options)

    # Automatically switch session state when a valid test is selected
    if selected_test == 'vo2max':
        st.session_state.test_section = False
        st.session_state.vo2max_test = True
        st.session_state.rmr_test = False
        st.rerun()
    elif selected_test == 'rmr':
        st.session_state.test_section = False
        st.session_state.vo2max_test = False
        st.session_state.rmr_test = True
        st.rerun()

if st.session_state.vo2max_test:
    # Placeholder for VO2max test implementation
    st.write("VO2max Test selected. Implement the logic here.")

    test = VO2MaxTest()
    name, _id = test.select_patient()

    if name:
        st.write(f"You selected patient: **{name}** (ID: `{_id}`)") # Replace with actual user_id

    if st.button("Back to Test Selection"):
        st.session_state.test_section = True
        st.session_state.vo2max_test = False
        st.rerun()
    

if st.session_state.rmr_test:
    # Placeholder for RMR test implementation
    st.write("RMR Test selected. Implement the logic here.")

    if st.button("Back to Test Selection"):
        st.session_state.test_section = True
        st.session_state.rmr_test = False
        st.rerun()
