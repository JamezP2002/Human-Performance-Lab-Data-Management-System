import streamlit as st
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import boto3

###################################
"""Report Viewer 
This page allows lab techs to search patients and view/download test reports
without editing access. Reports are fetched from AWS S3 and metadata from MongoDB."""
###################################

# ===============================
# Environment & MongoDB Setup
# ===============================
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
load_dotenv(dotenv_path)

database_credentials = os.getenv("database_credentials")
aws_access_key = os.getenv("aws_access_key_id")
aws_secret_key = os.getenv("aws_secret_access_key")
bucket_name = "champ-hpl-bucket"

client = MongoClient(database_credentials)
db = client['performance-lab']
users_col = db['users']
reports_col = db['reports']

# S3 setup
s3 = boto3.client("s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

# ===============================
# Report Viewer (Read-Only Access)
# ===============================
st.title("🧾 Lab Report Viewer (Read-Only)")

# --- Search Section ---
with st.expander("🔍 Search Clients", expanded=True):
    name_query = st.text_input("Enter client name to search")

    if name_query:
        query = {"Name": {"$regex": name_query, "$options": "i"}}
        patients = list(users_col.find(query))

        if patients:
            selected_patient = st.selectbox("Select Client", patients, format_func=lambda x: x['Name'])

            if selected_patient:
                st.markdown("### 🧑‍⚕️ Client Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Age:** {selected_patient.get('Age')} years")
                    st.markdown(f"**Sex:** {selected_patient.get('Sex')}")
                    st.markdown(f"**Doctor:** {selected_patient.get('Doctor', 'N/A')}")
                with col2:
                    st.markdown(f"**Height:** {selected_patient.get('Height', 'N/A')} in")
                    st.markdown(f"**Weight:** {selected_patient.get('Weight', 'N/A')} lb")

                # --- Test Reports Section ---
                test_reports = list(reports_col.find({"user_id": selected_patient["_id"]}))

                def format_report_entry(r):
                    test_type = r.get("test_type", "vo2max").upper()
                    date = r.get("test_date", {})
                    if isinstance(date, dict):
                        year = str(date.get("Year", ""))
                        month = str(date.get("Month", "")).zfill(2)
                        day = str(date.get("Day", "")).zfill(2)
                        month_map = {
                            "January": "01", "February": "02", "March": "03", "April": "04",
                            "May": "05", "June": "06", "July": "07", "August": "08",
                            "September": "09", "October": "10", "November": "11", "December": "12"
                        }
                        month = month_map.get(month, month)
                        date_str = f"{month}/{day}/{year}"
                    else:
                        date_str = "Unknown Date"

                    return f"{test_type} – {date_str}"

                if test_reports:
                    selected_report = st.selectbox(
                        "📄 Select Report",
                        test_reports,
                        format_func=format_report_entry
                    )

                    if selected_report:
                        st.markdown("---")
                        st.subheader("📋 Report Summary")
                        st.write(selected_report.get("summary", "No summary available."))

                        st.subheader("📥 Download Report PDF")

                        # Generate PDF file name for S3 retrieval
                        date_obj = selected_report.get("test_date", {})
                        if isinstance(date_obj, dict):
                            year = str(date_obj.get("Year", ""))
                            month = str(date_obj.get("Month", "")).zfill(2)
                            day = str(date_obj.get("Day", "")).zfill(2)
                            month_map = {
                                "January": "01", "February": "02", "March": "03", "April": "04",
                                "May": "05", "June": "06", "July": "07", "August": "08",
                                "September": "09", "October": "10", "November": "11", "December": "12"
                            }
                            month = month_map.get(month, month)
                            test_date_str = f"{year}-{month}-{day}"
                        else:
                            test_date_str = "unknown-date"

                        test_type = selected_report.get("test_type", "vo2max").lower()
                        clean_name = selected_patient['Name'].replace(',', '').replace(' ', '_')
                        pdf_filename = f"test_report_{clean_name}_{test_date_str}.pdf"
                        s3_key = f"reports/{pdf_filename}"

                        try:
                            with st.spinner("Downloading from S3..."):
                                s3.download_file(bucket_name, s3_key, pdf_filename)

                            with open(pdf_filename, "rb") as f:
                                st.download_button("📥 Download PDF", f, file_name=pdf_filename)

                        except Exception as e:
                            st.error(f"⚠️ Report not found in S3: {s3_key}")
                            st.exception(e)

                else:
                    st.info("No reports found for this patient.")
        else:
            st.warning("No matching clients found.")
