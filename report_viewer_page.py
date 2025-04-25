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
# Search clients
# ===============================
st.title("🧾 Lab Report Viewer (Read-Only)")

name_query = st.text_input("Search for a client by name")

if name_query:
    query = {"Name": {"$regex": name_query, "$options": "i"}}
    patients = list(users_col.find(query))

    if patients:
        selected_patient = st.selectbox("Select Client", patients, format_func=lambda x: x['Name'])

        if selected_patient:
            st.write("**Client Info:**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Age:** {selected_patient.get('Age')} years")
                st.markdown(f"**Sex:** {selected_patient.get('Sex')}")
                st.markdown(f"**Doctor:** {selected_patient.get('Doctor', 'N/A')}")
            with col2:
                st.markdown(f"**Height:** {selected_patient.get('Height', 'N/A')} in")
                st.markdown(f"**Weight:** {selected_patient.get('Weight', 'N/A')} lb")

            # ===============================
            # List Test Reports
            # ===============================
            test_reports = list(reports_col.find({"user_id": selected_patient["_id"]}))

            if test_reports:
                selected_report = st.selectbox(
                    "Select Report to View",
                    test_reports,
                    format_func=lambda r: f"{r.get('summary', 'Unnamed Report')} – {r.get('last_updated', '')}"
                )

                if selected_report:
                    st.markdown("---")
                    st.subheader("📋 Report Summary")
                    st.write(selected_report.get("summary", "No summary available."))

                    st.subheader("📥 Download Report PDF")
                    pdf_filename = f"test_report_{selected_patient['Name']}.pdf"
                    s3_key = f"reports/{pdf_filename}"

                    try:
                        # Stream the file from S3
                        with st.spinner("Downloading from S3..."):
                            s3.download_file(bucket_name, s3_key, pdf_filename)

                        with open(pdf_filename, "rb") as f:
                            st.download_button("Download PDF", f, file_name=pdf_filename)

                    except Exception as e:
                        st.error(f"Report not found in S3: {s3_key}")
                        st.exception(e)
            else:
                st.info("No reports found for this patient.")
    else:
        st.warning("No patients found with that name.")