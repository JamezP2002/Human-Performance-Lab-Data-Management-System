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
    selection = test.select_patient()

    if selection is not None:
        patient_info, test_protocol, results, df = selection

        st.subheader("🧍 Patient Info")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Name:** {patient_info.get('Name', 'N/A')}")
            st.markdown(f"**Age:** {patient_info.get('Age', 'N/A')} years")
            st.markdown(f"**Height:** {patient_info.get('Height', 'N/A'):.1f} cm")

        with col2:
            st.markdown(f"**Weight:** {patient_info.get('Weight', 'N/A'):.1f} kg")
            st.markdown(f"**Sex:** {patient_info.get('Sex', 'N/A')}")

        st.subheader("🏃 Test Protocol")

        col3, col4 = st.columns(2)

        with col3:
            st.markdown(f"**Test Degree:** {test_protocol.get('Test Degree', 'N/A')}")
            st.markdown(f"**Exercise Device:** {test_protocol.get('Exercise Device', 'N/A')}")

        test_env = test_protocol.get("Test Enviroment", {})
        best_vals = test_protocol.get("Best Sampling Values", {})
        results = results or {}

        st.subheader("📈 Test Results")

        col5, col6 = st.columns(2)

        with col5:
            st.markdown(f"**Max VO₂:** {results.get('Max VO2', 'N/A'):.2f} L/min")

        with col6:
            st.markdown(f"**VO₂max Percentile:** {results.get('VO2max Percentile', 'N/A')}")

        st.subheader("Plots")
        test.create_plots()

        if st.checkbox("Show raw tabular data"):
            st.dataframe(df)

        st.subheader("Summary Report")
        st.session_state.initial_report_text = st.text_area(
            "Enter your summary or interpretation:",
            value=st.session_state.get("initial_report_text", ""),
            height=150
        )

        if st.button("Next Step: Review Plots"):
            st.session_state.test_section = False
            st.session_state.vo2max_test = False
            st.session_state.rmr_test = False

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

    if st.button("Back to Test Selection"):
        st.session_state.test_section = True
        st.session_state.reviewing = False
        st.session_state.vo2max_test = False
        st.rerun()





























if st.session_state.rmr_test:
    # Placeholder for RMR test implementation
    st.write("RMR Test selected. WIP")

    if st.button("Back to Test Selection"):
        st.session_state.test_section = True
        st.session_state.rmr_test = False
        st.session_state.reviewing = False
        st.rerun()
