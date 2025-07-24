import pandas as pd
from pymongo import MongoClient
import streamlit as st
import os
from dotenv import load_dotenv

# find and load the .env file
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
#print(dotenv_path)  # Debugging
load_dotenv(dotenv_path)
database_credentials = os.getenv("database_credentials")

# connecting to mongodb 
client = MongoClient(database_credentials)
db = client['performance-lab']

# Users and Tests collections
users_collection = db['users']
tests_collection = db['vo2max']  

###########################################################################################
# Introduction #
###########################################################################################
st.title("This is a Report Uploader.")
st.write("This app will parse the VO2 Max report and store it in a MongoDB database.")
st.write("The report will be parsed into a dictionary and stored in the database.")
st.write("Upload a VO2 Max report in Excel format to get started.")

# Load the Excel file and do a test set
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

    ###########################################################################################
    # Unstructured Data #
    ###########################################################################################
    report_info_dict = {
        "School": df.iloc[0,0],
        "Date": {"Year": df.iloc[2, 1], "Month":df.iloc[2, 3], "Day": df.iloc[2, 5]},
        "Time": {"Hour": df.iloc[2, 6], "Minute": df.iloc[2, 8], "Second": df.iloc[2, 9]}
    }

    client_info_dict = {
        "Name": df.iloc[5, 1],
        "Age": df.iloc[6, 1],
        "Height": round(df.iloc[7, 3]),
        "Sex": df.iloc[6, 4],
        "Weight": round(df.iloc[7, 6]),
    }

    test_protocol_dict = {
        "Test Degree": df.iloc[11,1],
        "Exercise Device": df.iloc[12,1],
        "Test Enviroment": {
            "Insp. Temp": df.iloc[14,2], 
            "Baro. Pressure": df.iloc[14,5],
            "Insp. humid": df.iloc[14,8],
            "Exp. flow temp.": df.iloc[15, 1],
            "Insp. O2": df.iloc[16, 1],
            "Insp. CO2": df.iloc[16,4],
            "Selc. Flowmeter": df.iloc[17, 1],
            "STPD to BTPS": df.iloc[18, 1],
            "O2 Gain": df.iloc[18, 3],
            "CO2-NL gain": df.iloc[18, 5]
        },
        "Best Sampling Values": {
            "Base O2": df.iloc[21, 1],
            "Base CO2": df.iloc[21, 4],
            "Measured O2": df.iloc[21, 7],
            "Measured CO2": df.iloc[21, 10]
        }
    }

    ###########################################################################################
    # structured Data #
    ###########################################################################################

    start_row = 29
    end_row = start_row
    while end_row < len(df) and not (df.iloc[end_row, 0] == "End" or pd.isna(df.iloc[end_row, 0])):
        end_row += 1

    if df.iloc[start_row:end_row, 0:21].empty:
        st.write("No tabular data")
    else:
        if df.shape[1] > 19:
            tabular_data = df.iloc[start_row:end_row, 0:21]
            tabular_data.columns = [
                "Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE BTPS", "RER", "RR", "Vt BTPS",
                "FEO2", "FECO2", "HR", "TM SPD", "TM GRD", "AcKcal", "PetCO2", "PetO2", "VE/VCO2", "VE/VO2", "FATmin", "CHOmin"
            ]
        else:
            tabular_data = df.iloc[start_row:end_row, 0:19]
            tabular_data.columns = [
                "Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE BTPS", "RER", "RR", "Vt BTPS",
                "FEO2", "FECO2", "HR", "AcKcal", "PetCO2", "PetO2", "VE/VCO2", "VE/VO2", "FATmin", "CHOmin"
            ]

        tabular_data_dict = tabular_data.to_dict(orient="records")

        results_row = end_row + 2
        max_vo2_raw = df.iloc[results_row, 3]
        max_vo2 = round(float(max_vo2_raw), 2) if not pd.isna(max_vo2_raw) else None

        vo2_percentile_raw = df.iloc[results_row + 2, 1]
        if isinstance(vo2_percentile_raw, str):
            vo2_percentile = vo2_percentile_raw.split()[0]
        else:
            vo2_percentile = vo2_percentile_raw

        results_dict = {
            "Results": {"Max VO2": max_vo2}
        }
        if not pd.isna(vo2_percentile):
            results_dict["Results"]["VO2max Percentile"] = vo2_percentile

        test_protocol_dict.update(results_dict)

        name = client_info_dict["Name"]
        age = client_info_dict["Age"]
        sex = client_info_dict["Sex"]

        user = users_collection.find_one({"Name": name})
        if user:
            user_id = user["_id"]

            # Update any fields that may have changed (age, height, weight)
            updated_fields = {}

            if user.get("Age") != age:
                updated_fields["Age"] = age
            if user.get("Height") != client_info_dict["Height"]:
                updated_fields["Height"] = client_info_dict["Height"]
            if user.get("Weight") != client_info_dict["Weight"]:
                updated_fields["Weight"] = client_info_dict["Weight"]

            if updated_fields:
                users_collection.update_one(
                    {"_id": user_id},
                    {"$set": updated_fields}
                )
                st.info(f"✅ Client information updated: {', '.join(updated_fields.keys())}")
        else:
            new_user = {
                "Name": name,
                "Age": age,
                "Sex": sex,
                "Height": client_info_dict["Height"],
                "Weight": client_info_dict["Weight"],
                "test_ids": []
            }
            user_id = users_collection.insert_one(new_user).inserted_id

        test_document = {
            "user_id": user_id,
            "VO2 Max Report Info": {
                "Report Info": report_info_dict,
                "Client Info": client_info_dict,
                "Test Protocol": test_protocol_dict,
                "Tabular Data": tabular_data_dict
            }
        }
        test_result = tests_collection.insert_one(test_document)

        users_collection.update_one(
            {"_id": user_id},
            {"$push": {"test_ids": test_result.inserted_id}}
        )

    st.success(f"Test uploaded and linked to user: {name}")
    with st.expander("View Database Infomation", expanded=False):
        st.write("User ID:", user_id)
        st.write("Test Document ID:", test_result.inserted_id)
    
    with st.expander("View Report Information", expanded=False):
        st.subheader("Original DataFrame")
        st.dataframe(df)

        st.subheader("Report Data")
        st.write(report_info_dict)
        st.write(client_info_dict)
        st.write(test_protocol_dict)

        st.subheader("Tabular Data")
        st.write(tabular_data)
        
        st.subheader("Tabular Data Dictionary:")
        st.write(tabular_data_dict)

else:
    st.info("📂 Please upload an Excel file to begin.")


# Combine the dictionaries into one document
#document = {
#    "VO2 Max Report Info": {"Report Info": report_info_dict,
#                            "Patient Info": patient_info_dict,
#                            "Test Protocol": test_protocol_dict,
#                              "Tabular Data": tabular_data_dict}
#}
#print(test_protocol_dict)

#st.write("JSON Converted File:")
#st.write(document)

# Insert the document into MongoDB
#result = collection.insert_one(document)

# Print the inserted document's ID
#st.write("Document inserted with ID:", result.inserted_id)

# Retrieve the inserted document
#retrieved_doc = collection.find_one({"_id": result.inserted_id})
#print("Retrieved Document:", retrieved_doc)

