# questions to ask professor
# 1. Should I combine all this into a single nested dictionary?

import pandas as pd
from pymongo import MongoClient
import streamlit as st

# connecting to mongodb 
client = MongoClient('mongodb://localhost:27017/')
db = client['perfomanceLab']
collection = db['rmr']

# Load the Excel file and do a test set (just paitent infomation)
uploaded_file = st.file_uploader("Choose a file")
df = pd.read_excel(uploaded_file, header=None)

st.write("Original File:")
st.write(df)

###########################################################################################
# Unstructured Data #
###########################################################################################

# Extracting School Info
#school_info = df.iloc[0, :]
#print(school_info)

# Extracting Metabolic Text Report Info
#metabolic_info = df.iloc[2, 0:]
#print(metabolic_info)

# Extracting Patient Information
#patient_info = df.iloc[4:9, :9]  #row, cols
#print(patient_info)

# Convert sections to list of their respective dictionaries
report_info_dict = {
    "Test Number": df.iloc[0,9],
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
    "Height": df.iloc[7, 1],
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
                         "Exp. flow temp.": df.iloc[15, 3],
                         "Insp. O2": df.iloc[16, 1],
                         "Insp. CO2": df.iloc[16,4],
                         "Selc. Flowmeter": df.iloc[17, 1],
                         "STPD to BTPS": df.iloc[18, 1],
                         "O2 Gain": df.iloc[18, 3],
                         "CO2-NL gain": df.iloc[18, 5]},
    "Best Sampling Values": {"Base O2": df.iloc[21, 1],
                             "Base CO2": df.iloc[21, 4],
                             "Measured O2": df.iloc[21, 7],
                             "Measured CO2": df.iloc[21, 10]},
    "Results": {"Ave RMR":df.iloc[120, 9], 
                "Ave Kcal/kg.hr": df.iloc[120, 10]}
}

# Combine the dictionaries into one document
document = {
    "Metabolic Report Info": {"Report Info": report_info_dict,
                              "Patient Info": patient_info_dict,
                              "Test Protocol": test_protocol_dict}
}
#print(test_protocol_dict)

st.write("JSON Converted File:")
st.write(document)

# Insert the document into MongoDB
#result = collection.insert_one(document)

# Print the inserted document's ID
#print("Document inserted with ID:", result.inserted_id)

# Retrieve the inserted document
#retrieved_doc = collection.find_one({"_id": result.inserted_id})
#print("Retrieved Document:", retrieved_doc)

###########################################################################################
# structured Data #
###########################################################################################

if df.iloc[29:118, 0:11].empty:
    st.write("No tabular data")
else:
    tabular_data = df.iloc[29:118, 0:11]
    tabular_data.columns = ["Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE uncor.", "RQ", "FEO2", "FECO2", "REE", "RMR"]
    #print(tabular_data)

    st.write("Tabular Data:")
    st.write(tabular_data)


