import streamlit as st
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import boto3
import pandas as pd
from streamlit_pdf_viewer import pdf_viewer

###################################
"""This page allows lab techs to search clients and view/download test reports
without editing access. Reports are fetched from AWS S3 and metadata from MongoDB."""
###################################

# ===============================
# Environment & MongoDB Setup
# ===============================
load_dotenv()

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
        clients = list(users_col.find(query))

        if clients:
            selected_client = st.selectbox("Select Client", clients, format_func=lambda x: x['Name'])

            if selected_client:
                st.markdown("### 🧑‍⚕️ Client Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Age:** {selected_client.get('Age')} years")
                    st.markdown(f"**Sex:** {selected_client.get('Sex')}")
                with col2:
                    st.markdown(f"**Height:** {selected_client.get('Height', 'N/A')} in")
                    st.markdown(f"**Weight:** {selected_client.get('Weight', 'N/A')} lb")

                # --- Test Reports Section ---
                test_reports = list(reports_col.find({"user_id": selected_client["_id"]}))

                def format_report_entry(r):
                    test_type = r.get("test_type").upper()

                    # Format test date
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
                        test_date_str = f"{month}/{day}/{year}"
                    else:
                        test_date_str = "Unknown Date"

                    # Format last updated timestamp
                    last_updated = r.get("last_updated")
                    if last_updated:
                        last_updated_str = pd.to_datetime(last_updated).strftime("%m/%d/%Y")
                    else:
                        last_updated_str = "Unknown Update"

                    return f"{test_type} – Test Date: {test_date_str} – Updated: {last_updated_str}"

                if test_reports:
                    selected_report = st.selectbox(
                        "📄 Select Report",
                        test_reports,
                        format_func=format_report_entry
                    )

                    if selected_report:
                        st.markdown("---")
                        
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

                        test_type = selected_report.get("test_type").upper()
                        clean_name = selected_client['Name'].replace(',', '').replace(' ', '_')
                        pdf_filename = f"{test_type}_report_{clean_name}_{test_date_str}.pdf"
                        s3_key = f"reports/{pdf_filename}"

                        st.subheader("📋 Report")

                        # Getting the PDF from S3 to view it
                        url = s3.generate_presigned_url(
                            "get_object",
                            Params={"Bucket": bucket_name, "Key": s3_key},
                            ExpiresIn=600
                        )

                        st.markdown(f"""
                        <iframe src="{url}" width="100%" height="800px" type="application/pdf"></iframe>
                        """, unsafe_allow_html=True)
                        
                        #pdf_viewer(url) 

                        try:
                            with st.spinner("Downloading from S3..."):
                                s3.download_file(bucket_name, s3_key, pdf_filename)

                            with open(pdf_filename, "rb") as f:
                                st.download_button("📥 Download PDF", f, file_name=pdf_filename)

                        except Exception as e:
                            st.error(f"⚠️ Report not found in S3: {s3_key}")
                            st.exception(e)

                else:
                    st.info("No reports found for this client.")
        else:
            st.warning("No matching clients found.")
