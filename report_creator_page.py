from pymongo import MongoClient
import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd

# loading tests
from vo2max_test import VO2MaxTest
from rmr_test import RMRTest

TEST_CLASS_MAP = {
    "VO2_MAX": VO2MaxTest,
    "RMR":      RMRTest,
}

###################################
"""Human Performance Lab Report Builder
This is the streamlit app for building and reviewing reports based on tests.
As of right now, it supports VO2 Max tests. It allows users to select a client,
choose a test, and either generate a new report or edit an existing one."""
###################################

# ===============================
# Setup: Environment & Database
# ===============================

# Load environment variables (MongoDB URI, etc.)
load_dotenv()
database_credentials = os.getenv("database_credentials")

# Connect to MongoDB
client = MongoClient(database_credentials)
db = client['performance-lab']
users_col = db['users']
reports_col = db['reports']
vo2_col = db['vo2max']  # Collection for VO2 Max tests (expandable for other test types)

# ===============================
# Session State Initialization
# ===============================

# These keys help maintain state across page interactions
for key in ['test_section', 'report_builder', 'reviewing', 'selected_test', 'selected_client', 'plot_comments', 'plot_includes']:
    if key not in st.session_state:
        st.session_state[key] = False if key in ['test_section', 'report_builder', 'reviewing'] else {}

# ===============================
# client Selection Page
# ===============================
if not st.session_state['report_builder'] and not st.session_state['reviewing']:
    st.title("🏃‍♂️ Human Performance Lab Report Builder")

    with st.expander("🔍 Client Select", expanded=True):
        name_query = st.text_input("Search for a client by name")

        if name_query:
            # Search MongoDB for clients matching the query
            query = {"Name": {"$regex": name_query, "$options": "i"}}
            clients = list(users_col.find(query))

            if clients:
                selected_client = st.selectbox("Select Client", clients, format_func=lambda x: x['Name'])

                if selected_client:
                    st.session_state.selected_client = selected_client

                    # ===============================
                    # Display Selected Client Info
                    # ===============================
                    st.write("**Client Info:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Age:** {selected_client.get('Age')} years")
                        st.markdown(f"**Sex:** {selected_client.get('Sex')}")
                    with col2:
                        st.markdown(f"**Height:** {selected_client.get('Height', 'N/A')} in")
                        st.markdown(f"**Weight:** {selected_client.get('Weight', 'N/A')} lb")

                    # ===============================
                    # Step 2: Test Selection
                    # ===============================
                    tests = list(vo2_col.find({"user_id": selected_client["_id"]}))

                    def format_test_entry(t):
                        test_type = t.get('test_type', 'vo2max').upper()
                        date_obj = t.get('VO2 Max Report Info', {}).get('Report Info', {}).get('Date', {})
                        if isinstance(date_obj, dict):
                            year = str(date_obj.get("Year", ""))
                            month = str(date_obj.get("Month", "")).zfill(2)  # Zero-pad if numeric
                            day = str(date_obj.get("Day", "")).zfill(2)
                            # Optional: convert month names to numbers
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month = month_map.get(month, month)  # Convert if needed
                            formatted_date = f"{month}/{day}/{year}"
                        else:
                            formatted_date = "Unknown Date"

                        return f"{test_type} – Test Date: {formatted_date}"

                    if tests:
                        selected_test = st.selectbox("Select Test", tests, format_func=format_test_entry)

                        # Check if a report already exists for this test
                        report_exists = reports_col.find_one({
                            "user_id": selected_client["_id"],
                            "test_id": selected_test["_id"]
                        })

                        # ===============================
                        # Step 3: Action Buttons
                        # ===============================
                        col1, col2 = st.columns(2)

                        # Left column: Edit existing or generate new
                        with col1:
                            if report_exists:
                                last_updated = report_exists.get("last_updated")
                                if last_updated:
                                    last_updated_str = pd.to_datetime(last_updated).strftime("%m/%d/%Y")
                                    edit_button_label = f"✏️ Edit Existing Report (Last Updated: {last_updated_str})"
                                else:
                                    edit_button_label = "✏️ Edit Existing Report"

                                if st.button(edit_button_label):
                                    st.session_state.selected_test = selected_test
                                    st.session_state.report_builder = True
                                    st.session_state.test_section = False
                                    st.session_state.reviewing = False
                                    st.session_state.report_loaded = False
                                    st.rerun()

                            else:
                                if st.button("📄 Generate Report"):
                                    st.session_state.selected_test = selected_test
                                    st.session_state.report_builder = True
                                    st.session_state.test_section = False
                                    st.session_state.reviewing = False
                                    st.session_state.report_loaded = False
                                    st.rerun()

                        # Right column: Overwrite existing report
                        with col2:
                            if report_exists:
                                if st.button("📄 Start New Report (Overwrite)"):
                                    reports_col.delete_one({
                                        "user_id": selected_client["_id"],
                                        "test_id": selected_test["_id"]
                                    })
                                    st.session_state.selected_test = selected_test
                                    st.session_state.report_builder = True
                                    st.session_state.test_section = False
                                    st.session_state.reviewing = False
                                    st.session_state.report_loaded = False
                                    st.success("🗑️ Previous report deleted. Starting fresh.")
                                    st.rerun()
                            else:
                                st.info("No report found for this client for this test.")
            else:
                st.warning("No matching client found.")

# ===============================
# Report Builder Section for VO2 Max Tests
# ===============================
if st.session_state['report_builder']:
    st.subheader("📝 Report Builder")
    st.write("Building report for:", st.session_state.selected_client['Name'])

    # Retrieve the selected test and initialize the appropriate test class
    test_data = st.session_state.selected_test
    test = VO2MaxTest()  # Eventually can be dynamic based on test_type
    selection = test.parse_test(test_data)

    if selection:
        client_info, test_protocol, results, df = selection  # Unpack parsed test data

        # Load saved report (from MongoDB) only once per session unless rerun
        if 'report_loaded' not in st.session_state:
            loaded = test.load_saved_report()
            if loaded:
                st.success("✅ Loaded existing saved report for editing.")
            else:
                st.info("No saved report found. Starting fresh.")
            st.session_state.report_loaded = True

        # ===============================
        # client Information Display
        # ===============================
        st.subheader("client Info")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {client_info.get('Name', 'N/A')}")
            st.markdown(f"**Age:** {client_info.get('Age', 'N/A')} years")
            st.markdown(f"**Sex:** {client_info.get('Sex', 'N/A')}")
        with col2:
            st.markdown(f"**Weight:** {client_info.get('Weight', 'N/A'):.1f} lb")
            st.markdown(f"**Height:** {client_info.get('Height', 'N/A'):.1f} in")

        # ===============================
        # Test Protocol Section
        # ===============================
        st.subheader("Test Protocol")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f"**Test Degree:** {test_protocol.get('Test Degree', 'N/A')}")
            st.markdown(f"**Exercise Device:** {test_protocol.get('Exercise Device', 'N/A')}")

        # ===============================
        # Results Section
        # ===============================
        st.subheader("Results")
        col5, col6 = st.columns(2)
        with col5:
            st.markdown(f"**Max VO₂:** {results.get('Max VO2', 'N/A'):.2f} ML/min")
        with col6:
            st.markdown(f"**VO₂max Percentile:** {results.get('VO2max Percentile', 'N/A')}")

        # Optional: Display full test data as raw dataframe
        if st.checkbox("Show raw tabular data"):
            st.dataframe(df)

        # ===============================
        # Dynamic Plots & Comment Boxes
        # ===============================
        st.markdown(f"---")
        plots = test.report_builder()  # Generates visual plots + comment boxes

        # ===============================
        # Navigation Button
        # ===============================
        if st.button("Back to Client Select"):
            # Reset builder state and return to the client/test selection page
            for key in ['report_builder', 'report_loaded', 'selected_test', 'selected_client']:
                st.session_state[key] = None if key.startswith('selected') else False
            st.rerun()


# ===============================
# Review Report Section
# ===============================
if st.session_state['reviewing']:
    st.subheader("📊 Review Report")
    st.write(f"Reviewing report for {st.session_state.selected_client['Name']}")

    # Initialize the appropriate test class for review (VO2Max only for now)
    test = VO2MaxTest()
    test.review_report(test_data=st.session_state.selected_test)

    # Button to go back to selection screen
    if st.button("Back to client Select"):
        st.session_state.reviewing = False
        st.session_state.selected_test = None
        st.session_state.selected_client = None
        st.rerun()