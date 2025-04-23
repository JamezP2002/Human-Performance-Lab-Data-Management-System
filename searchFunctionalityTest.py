from pymongo import MongoClient
import streamlit as st
import os
from dotenv import load_dotenv
from vo2max_test import VO2MaxTest

# Load environment variables
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
load_dotenv(dotenv_path)
database_credentials = os.getenv("database_credentials")

# Connect to MongoDB
client = MongoClient(database_credentials)
db = client['performance-lab']
users_col = db['users']
reports_col = db['reports']
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
                    st.json({
                        "Age": selected_patient.get("Age"),
                        "Sex": selected_patient.get("Sex"),
                        "Height": selected_patient.get("Height"),
                        "Weight": selected_patient.get("Weight"),
                        "Doctor": selected_patient.get("Doctor")
                    })

                    # Find all tests
                    tests = list(vo2_col.find({"user_id": selected_patient["_id"]}))
                    if tests:
                        selected_test = st.selectbox("Select Test", tests, format_func=lambda t: t['VO2 Max Report Info']['Report Info'].get('Date', 'Unknown Date'))

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

# Report Builder Section
if st.session_state['report_builder']:
    st.subheader("📝 Report Builder")
    st.write("Building report for:", st.session_state.selected_patient['Name'])

    test_data = st.session_state.selected_test
    test = VO2MaxTest()
    selection = test.parse_existing_test(test_data)

    if selection:
        patient_info, test_protocol, results, df = selection

        if 'report_loaded' not in st.session_state:
            loaded = test.load_saved_report()
            if loaded:
                st.success("✅ Loaded existing saved report for editing.")
            else:
                st.info("No saved report found. Starting fresh.")
            st.session_state.report_loaded = True

        st.subheader("Patient Info")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {patient_info.get('Name', 'N/A')}")
            st.markdown(f"**Age:** {patient_info.get('Age', 'N/A')} years")
            st.markdown(f"**Height:** {patient_info.get('Height', 'N/A'):.1f} cm")
        with col2:
            st.markdown(f"**Weight:** {patient_info.get('Weight', 'N/A'):.1f} kg")
            st.markdown(f"**Sex:** {patient_info.get('Sex', 'N/A')}")

        st.subheader("Test Protocol")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f"**Test Degree:** {test_protocol.get('Test Degree', 'N/A')}")
            st.markdown(f"**Exercise Device:** {test_protocol.get('Exercise Device', 'N/A')}")

        st.subheader("Results")
        col5, col6 = st.columns(2)
        with col5:
            st.markdown(f"**Max VO₂:** {results.get('Max VO2', 'N/A'):.2f} L/min")
        with col6:
            st.markdown(f"**VO₂max Percentile:** {results.get('VO2max Percentile', 'N/A')}")

        if st.checkbox("Show raw tabular data"):
            st.dataframe(df)

        # Render and comment on plots
        st.markdown(f"---")
        plots = test.report_builder()

        if st.button("Back to Patient Select"):
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