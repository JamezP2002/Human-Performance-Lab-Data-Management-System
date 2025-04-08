from pymongo import MongoClient
import streamlit as st
import os
from dotenv import load_dotenv
import boto3
import matplotlib.pyplot as plt
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
if 'reviewing' not in st.session_state:
    st.session_state.reviewing = False

# Navigation logic
def go_to_vo2max():
    st.session_state.test_section = False
    st.session_state.vo2max_test = True
    st.session_state.rmr_test = False
    st.session_state.reviewing = False

def go_to_rmr():
    st.session_state.test_section = False
    st.session_state.vo2max_test = False
    st.session_state.rmr_test = True
    st.session_state.reviewing = False

# Main app logic based on session state
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
        st.session_state.reviewing = False
        st.rerun()
    elif selected_test == 'rmr':
        st.session_state.test_section = False
        st.session_state.vo2max_test = False
        st.session_state.rmr_test = True
        st.session_state.reviewing = False
        st.rerun()

# 2. VO2Max Test Section
if st.session_state.vo2max_test:
    st.write("VO2max Test selected. Please select a patient from the dropdown above to proceed.")

    test = VO2MaxTest()
    patient_info, test_protocol, results, df = test.select_patient()

    # Display patient details
    st.subheader("Patient Info")
    st.write(patient_info)

    st.subheader("Test Protocol")
    st.write(test_protocol)

    st.subheader("Plots")
    test.create_plots()

    if st.checkbox("Show raw tabular data"):
        st.dataframe(df)

    if st.button("Next Step: Review Plots"):
        # Clear VO2max-related states
        st.session_state.test_section = False
        st.session_state.vo2max_test = False
        st.session_state.rmr_test = False

        # Set review state
        st.session_state.reviewing = True
        st.session_state.plot_index = 0
        st.session_state.plot_comments = {}
        st.rerun()

    if st.button("Back to Test Selection"):
        st.session_state.test_section = True
        st.session_state.vo2max_test = False
        st.rerun()

# 3. Review Report Page
if st.session_state.reviewing:
    st.write("Reviewing VO2max Test Plots")
    st.subheader("Review Plots")

    test = VO2MaxTest()
    test.review_report()





























if st.session_state.rmr_test:
    # Placeholder for RMR test implementation
    st.write("RMR Test selected. WIP")

    if st.button("Back to Test Selection"):
        st.session_state.test_section = True
        st.session_state.rmr_test = False
        st.session_state.reviewing = False
        st.rerun()
