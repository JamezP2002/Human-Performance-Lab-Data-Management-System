from pymongo import MongoClient
import streamlit as st
import os
from dotenv import load_dotenv
from vo2max_test import VO2MaxTest

###################################
"""Human Performance Lab Report Builder
This is the streamlit app for building and reviewing reports based on tests.
As of right now, it supports VO2 Max tests. It allows users to select a patient,
choose a test, and either generate a new report or edit an existing one."""
###################################

# Load environment variables
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
load_dotenv(dotenv_path)
database_credentials = os.getenv("database_credentials")

# Connect to MongoDB
client = MongoClient(database_credentials)
db = client['performance-lab']
users_col = db['users']
reports_col = db['reports']

# future tests will be added here
vo2_col = db['vo2max']

# Initialize session state
for key in ['test_section', 'report_builder', 'reviewing', 'selected_test', 'selected_patient', 'plot_comments', 'plot_includes']:
    if key not in st.session_state:
        st.session_state[key] = False if key in ['test_section', 'report_builder', 'reviewing'] else {}

# Patient Select Section
if not st.session_state['report_builder'] and not st.session_state['reviewing']:
    st.title("🏃‍♂️ Human Performance Lab Report Builder")
    with st.expander("🔍 Patient Select", expanded=True):
        name_query = st.text_input("Search for a patient by name")

        if name_query:
            query = {"Name": {"$regex": name_query, "$options": "i"}}
            patients = list(users_col.find(query))

            if patients:
                selected_patient = st.selectbox("Select Patient", patients, format_func=lambda x: x['Name'])

                if selected_patient:
                    st.session_state.selected_patient = selected_patient
                    st.write("**Patient Info:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Age:** {selected_patient.get('Age')} years")
                        st.markdown(f"**Sex:** {selected_patient.get('Sex')}")
                        st.markdown(f"**Height:** {selected_patient.get('Height', 'N/A')} in")
                    with col2:
                        st.markdown(f"**Weight:** {selected_patient.get('Weight', 'N/A')} lb")
                        st.markdown(f"**Doctor:** {selected_patient.get('Doctor', 'N/A')}")

                    # Find all tests (VO2 Max ATM)
                    tests = list(vo2_col.find({"user_id": selected_patient["_id"]}))

                    # Can be used for expanded tests in the future
                    def format_test_entry(t):
                        test_type = t.get('test_type', 'vo2max').upper()  # default to VO2MAX for now
                        date = t.get('VO2 Max Report Info', {}).get('Report Info', {}).get('Date', 'Unknown Date')
                        return f"{test_type} - {date}"

                    if tests:
                        selected_test = st.selectbox("Select Test", tests, format_func=format_test_entry)

                # Check if there's already a saved report
                report_exists = reports_col.find_one({
                    "user_id": selected_patient["_id"],
                    "test_id": selected_test["_id"]
                })

                col1, col2 = st.columns(2)

                with col1:
                    if report_exists:
                        if st.button("✏️ Edit Existing Report"):
                            st.session_state.selected_test = selected_test
                            st.session_state.report_builder = True
                            st.session_state.test_section = False
                            st.session_state.reviewing = False
                            st.session_state.report_loaded = False  # So it reloads from MongoDB
                            st.rerun()
                    else:
                        if st.button("📄 Generate Report"):
                            st.session_state.selected_test = selected_test
                            st.session_state.report_builder = True
                            st.session_state.test_section = False
                            st.session_state.reviewing = False
                            st.session_state.report_loaded = False
                            st.rerun()

                with col2:
                    if report_exists:
                        if st.button("📄 Start New Report (Overwrite)"):
                            # You could also add a confirm checkbox for safety
                            reports_col.delete_one({
                                "user_id": selected_patient["_id"],
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
                        st.info("No report found for this patient for this test.")
            else:
                st.warning("No matching patient found.")

# ===============================
# Report Builder Section for VO2 Max Tests
# ===============================
if st.session_state['report_builder']:
    st.subheader("📝 Report Builder")
    st.write("Building report for:", st.session_state.selected_patient['Name'])

    # Retrieve the selected test and initialize the appropriate test class
    test_data = st.session_state.selected_test
    test = VO2MaxTest()  # Eventually can be dynamic based on test_type
    selection = test.parse_test(test_data)

    if selection:
        patient_info, test_protocol, results, df = selection  # Unpack parsed test data

        # Load saved report (from MongoDB) only once per session unless rerun
        if 'report_loaded' not in st.session_state:
            loaded = test.load_saved_report()
            if loaded:
                st.success("✅ Loaded existing saved report for editing.")
            else:
                st.info("No saved report found. Starting fresh.")
            st.session_state.report_loaded = True

        # ===============================
        # Patient Information Display
        # ===============================
        st.subheader("Patient Info")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {patient_info.get('Name', 'N/A')}")
            st.markdown(f"**Age:** {patient_info.get('Age', 'N/A')} years")
            st.markdown(f"**Height:** {patient_info.get('Height', 'N/A'):.1f} cm")
        with col2:
            st.markdown(f"**Weight:** {patient_info.get('Weight', 'N/A'):.1f} kg")
            st.markdown(f"**Sex:** {patient_info.get('Sex', 'N/A')}")

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
            st.markdown(f"**Max VO₂:** {results.get('Max VO2', 'N/A'):.2f} L/min")
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
        if st.button("Back to Patient Select"):
            # Reset builder state and return to the patient/test selection page
            for key in ['report_builder', 'report_loaded', 'selected_test', 'selected_patient']:
                st.session_state[key] = None if key.startswith('selected') else False
            st.rerun()


# Step 3: Review Report Page
if st.session_state['reviewing']:
    st.subheader("📊 Review Report")
    st.write(f"Reviewing report for {st.session_state.selected_patient['Name']}")

    test = VO2MaxTest()
    test.review_report(test_data=st.session_state.selected_test)

    if st.button("Back to Patient Select"):
        st.session_state.reviewing = False
        st.session_state.selected_test = None
        st.session_state.selected_patient = None
        st.rerun()