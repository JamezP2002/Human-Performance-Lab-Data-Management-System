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
collection = db['vo2max']

###########################################################################################
# Introduction #
###########################################################################################
st.title("This is a VO2 Max Report Uploader.")
st.write("This app will parse the VO2 Max report and store it in a MongoDB database.")
st.write("The report will be parsed into a dictionary and stored in the database.")
st.write("Upload a VO2 Max report in Excel format to get started.")

# Load the Excel file and do a test set
uploaded_file = st.file_uploader("Choose a file")
df = pd.read_excel(uploaded_file, header=None, engine="xlrd")

st.title("Original File:")
st.dataframe(df)
# if we wanna hide the original data
#if st.checkbox("Show raw original data"):
#    st.dataframe(df)

###########################################################################################
# Unstructured Data #
###########################################################################################

# Convert sections to list of their respective dictionaries
report_info_dict = {
    "School": df.iloc[0,0],
    "Date": {"Year": df.iloc[2, 1],
            "Month":df.iloc[2, 3],
            "Day": df.iloc[2, 5]},
    "Time": {"Hour": df.iloc[2, 6], 
             "Minute": df.iloc[2, 8], 
             "Second": df.iloc[2, 9]}}

patient_info_dict = {
    "File Number": df.iloc[5, 3],
    "Name": df.iloc[5, 1],
    "Age": df.iloc[6, 1],
    "Height": df.iloc[7, 3],
    "Sex": df.iloc[6, 4],
    "Weight": df.iloc[7, 6],
    "Doctor": df.iloc[5, 5],    
}

test_protocol_dict = {
    "Test Degree": df.iloc[11,1],
    "Exercise Device": df.iloc[12,1],
    "Test Enviroment": {"Insp. Temp": df.iloc[14,2], 
                        "Baro. Pressure": df.iloc[14,5],
                         "Insp. humid": df.iloc[14,8],
                         "Exp. flow temp.": df.iloc[15, 1],
                         "Insp. O2": df.iloc[16, 1],
                         "Insp. CO2": df.iloc[16,4],
                         "Selc. Flowmeter": df.iloc[17, 1],
                         "STPD to BTPS": df.iloc[18, 1],
                         "O2 Gain": df.iloc[18, 3],
                         "CO2-NL gain": df.iloc[18, 5]},
    "Best Sampling Values": {"Base O2": df.iloc[21, 1],
                             "Base CO2": df.iloc[21, 4],
                             "Measured O2": df.iloc[21, 7],
                             "Measured CO2": df.iloc[21, 10]}
}

#st.write(report_info_dict)
#st.write(patient_info_dict)
#st.write(test_protocol_dict)

###########################################################################################
# structured Data #
###########################################################################################

# Finding the start and end of the tabular data (dynamicly)
start_row = 29
end_row = start_row
while end_row < len(df) and not (df.iloc[end_row, 0] == "End" or pd.isna(df.iloc[end_row, 0])):
    end_row += 1

# Check if the tabular data is empty
if df.iloc[start_row:end_row, 0:21].empty:
    st.write("No tabular data")
else:
    # checking if the tabular data has more than 19 columns
    if df.shape[1] > 19: # if it does, it runs as standard
        tabular_data = df.iloc[start_row:end_row, 0:21]
        tabular_data.columns = ["Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE BTPS", "RER", "RR", "Vt BTPS", "FEO2", "FECO2", "HR", "TM SPD", "TM GRD", "AcKcal", "PetCO2", "PetO2", "VE/VCO2", "VE/VO2", "FATmin", "CHOmin"]
    # checking if the tabular data has less than 19 columns
    # if it does, it drops "TM SPD", "TM GRD"
    else:
        tabular_data = df.iloc[start_row:end_row, 0:19]
        tabular_data.columns = ["Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE BTPS", "RER", "RR", "Vt BTPS", "FEO2", "FECO2", "HR", "AcKcal", "PetCO2", "PetO2", "VE/VCO2", "VE/VO2", "FATmin", "CHOmin"]

tabular_data_dict = tabular_data.to_dict(orient="records")
#st.write("Tabular Data Dictionary:")
#st.write(tabular_data_dict)

############################
## More dynamic filtering ##
############################

# Find the start of the results section dynamically
results_row = end_row + 2

results_dict = {
    "Results": {"Max VO2": df.iloc[results_row, 1]}
}

# Checking if VO2max Percentile is empty
if not pd.isna(df.iloc[results_row + 2, 1]):
    results_dict["Results"]["VO2max Percentile"] = df.iloc[results_row + 2, 1]

# Add the results back to the test_protocol_dict
test_protocol_dict.update(results_dict)

# printing out the data all formated
st.title("Report Data")
st.write(report_info_dict)
st.write(patient_info_dict)
st.write(test_protocol_dict)
st.title("Tabular Data")
st.write(tabular_data)
st.title("Tabular Data Dictionary:")
st.write(tabular_data_dict)

###########################################################################################
# MongoDB #
###########################################################################################

# Combine the dictionaries into one document
document = {
    "VO2 Max Report Info": {"Report Info": report_info_dict,
                            "Patient Info": patient_info_dict,
                            "Test Protocol": test_protocol_dict,
                              "Tabular Data": tabular_data_dict}
}
#print(test_protocol_dict)

#st.write("JSON Converted File:")
#st.write(document)

# Insert the document into MongoDB
result = collection.insert_one(document)

# Print the inserted document's ID
st.write("Document inserted with ID:", result.inserted_id)

# Retrieve the inserted document
#retrieved_doc = collection.find_one({"_id": result.inserted_id})
#print("Retrieved Document:", retrieved_doc)