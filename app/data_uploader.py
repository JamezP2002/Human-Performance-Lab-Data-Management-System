import pandas as pd
from pymongo import MongoClient
import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime

# find and load the .env file
dotenv_path = os.path.abspath(os.path.join("human-peformance-lab-capstone/.env"))
#print(dotenv_path)  # Debugging
load_dotenv(dotenv_path)
database_credentials = os.getenv("database_credentials")

# connecting to mongodb 
client = MongoClient(database_credentials)
db = client['performance-lab']

# Users and Tests collections
users_collection = db['users']
tests_collection = db['tests']

# import parser classes
from ingest.vo2max_ingest import VO2MaxParser 
from ingest.rmr_ingest import RMRParser

rmr_params = ["Rest"]
vo2max_params = ["Maximal"]

###########################################################################################
# Introduction 
###########################################################################################
st.title("Data Uploader")
st.write("This app will parse the raw excel data and store it in a MongoDB database.")
st.write("The raw excel data will be parsed into a dictionary and stored in the database.")
st.write("Upload a VO2 Max or RMR data in Excel format to get started.")

tab1, tab2 = st.tabs(["Upload Data", "View Data"])

with tab1:
    # Load the Excel file check which type of data it is
    uploaded_file = st.file_uploader("Choose a file")

    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower()

        try:
            if file_type == "xls":
                df = pd.read_excel(uploaded_file, header=None, engine="xlrd")
            elif file_type == "xlsx":
                df = pd.read_excel(uploaded_file, header=None, engine="openpyxl")
            else:
                st.error("Unsupported file type. Please upload a .xls or .xlsx file.")
        except Exception as e:
            st.error(f"Failed to read Excel file: {e}")

        try:
            test_degree = df.iloc[11, 1]     
            test_degree_label = str(test_degree).strip()
            #st.success(f"Test Degree: {test_degree_label}")
            parse_param = [test_degree_label]

            if parse_param == rmr_params:
                st.success("RMR data detected.")
                parser = RMRParser(df)
                report_name = "RMR Report Info"
                report_type = "RMR"
            elif parse_param == vo2max_params:
                st.success("VO2 Max data detected.")
                #st.write("Processing VO2 Max data...")
                parser = VO2MaxParser(df)
                report_name = "VO2 Max Report Info"
                report_type = "VO2 Max"
            else:
                st.error("Unsupported data type. Please upload a valid RMR or VO2 Max data file.")

            parsed = parser.parse()
            #st.write(parsed) 

            # Extracting parsed data
            report_info   = parsed["Report Info"]
            client_info   = parsed["Client Info"]
            test_protocol = parsed["Test Protocol"]
            tabular_data  = parsed["Tabular Data"]

            name   = client_info["Name"]
            age    = client_info["Age"]
            height = client_info["Height"]
            weight = client_info["Weight"]

            # Updating the user
            user = users_collection.find_one({"Name": name})
            if user:
                user_id = user["_id"]
                # check for any changed fields
                updates = {}
                if user.get("Age")    != age:    updates["Age"]    = age
                if user.get("Height") != height: updates["Height"] = height
                if user.get("Weight") != weight: updates["Weight"] = weight

                if updates:
                    users_collection.update_one({"_id": user_id}, {"$set": updates})
                    st.info(f"Updated user fields: {', '.join(updates)}")
            else:
                user_doc = {
                    "Name":   name,
                    "Age":    age,
                    "Sex":    client_info["Sex"],
                    "Height": height,
                    "Weight": weight,
                    "test_ids": []
                }
                user_id = users_collection.insert_one(user_doc).inserted_id
                st.info(f"Created new user: {name}")

            test_document = {
                "user_id": user_id,
                "test_type": report_type,
                "Upload Date": datetime.utcnow(),
                f"{report_name}": {
                    "Report Info":   report_info,
                    "Client Info":   client_info,
                    "Test Protocol": test_protocol,
                    "Tabular Data":  tabular_data
                }
            }
            test_result = tests_collection.insert_one(test_document)

            # Link it back to the user
            users_collection.update_one(
                {"_id": user_id},
                {"$push": {"test_ids": test_result.inserted_id}}
            )

            # Feedback to the user
            st.success(f"Test uploaded and linked to user: {name}")
        except Exception as e:
            st.error(f"Could not read cells: {e}")

        with tab2:
            st.header("View Database Information")
            st.write("User ID:", user_id)
            st.write("Test Document ID:", test_result.inserted_id)

            st.header("View Report Data")
            st.subheader("Report Info")
            st.write(report_info)

            st.subheader("Client Info")
            st.write(client_info)

            st.subheader("Test Protocol")
            st.write(test_protocol)

            st.subheader("Tabular Data")
            st.write(tabular_data)

    else:
        st.info("📂 Please upload an Excel file to begin.")