import pandas as pd
from pymongo import MongoClient
import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv, find_dotenv

# find and load the .env file
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
#print(dotenv_path)  # Debugging
load_dotenv(dotenv_path)
database_credentials = os.getenv("database_credentials")

# connecting to mongodb 
#st.write("Connecting to database...")
client = MongoClient(database_credentials)
db = client['performance-lab']
collection = db['vo2max']
#st.write("Connected to database, retrieving the data.")

# create a dropdown menu for the patient name to select the document to load
st.write("Choose a patient to load.")
documents = list(collection.find())
patient_names = [doc["VO2 Max Report Info"]["Patient Info"]["Name"] for doc in documents]
selected_name = st.selectbox("Select Patient Name", patient_names)
document = next(doc for doc in documents if doc["VO2 Max Report Info"]["Patient Info"]["Name"] == selected_name)
st.write("Document loaded, extracting the data of: ", selected_name)

# Extract Tabular Data
tabular_data = document["VO2 Max Report Info"]["Tabular Data"]

# Convert to DataFrame (allow it to be hidden)
df = pd.DataFrame(tabular_data)
if st.checkbox("Show raw tabular data"):
    st.dataframe(df)

# Plot V-Slope
plt.figure(figsize=(10, 5))
plt.scatter(df['VO2 STPD'], df['VCO2 STPD'], label='V-Slope', marker='o')
plt.xlabel("VO2 STPD (mL/min)")
plt.ylabel("VCO2 STPD (mL/min)")
plt.title("V-Slope")
plt.legend()
plt.grid()
st.pyplot(plt)

# Plot VO2 ml
plt.figure(figsize=(10, 5))
plt.scatter(df['Time'], df['VO2 STPD'], label='VO2 ml', marker='o')
plt.xlabel("Time (minutes)")
plt.ylabel("Volume (mL/min)")
plt.title("VO2 ml over Time")
plt.legend()
plt.grid()
st.pyplot(plt)

# Plot HR scatter
plt.figure(figsize=(10, 5))
plt.scatter(df['Time'], df['HR'], label='HR', marker='o')
plt.xlabel("Time (minutes)")
plt.ylabel("Heart Rate (bpm)")
plt.title("Heart Rate over Time")
plt.legend()
plt.grid()
st.pyplot(plt)

# Plot Fat and CHO Ox
plt.figure(figsize=(10, 5))
plt.scatter(df['Time'], df['FATmin'], label='Fat Ox', marker='o')
plt.scatter(df['Time'], df['CHOmin'], label='CHO Ox', marker='s')
plt.xlabel("Time (minutes)")
plt.ylabel("Oxidation Rate (g/min)")
plt.title("Fat and CHO Ox over Time")
plt.legend()
plt.grid()
st.pyplot(plt)

# Plot Ventilatory Equivalents & End Tidal CO2 Tension
plt.figure(figsize=(10, 5))
plt.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o')
plt.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='s')
plt.scatter(df['Time'], df['PetCO2'], label='PetCO2', marker='^')
plt.xlabel("Time (minutes)")
plt.ylabel("Volume (mL/min)")
plt.title("Ventilatory Equivalents & End Tidal CO2 Tension over Time")
plt.legend()
plt.grid()
st.pyplot(plt)

# Plot Ventilatory Equivalents & End Tidal O2 Tension
plt.figure(figsize=(10, 5))
plt.scatter(df['Time'], df['VE/VO2'], label='FEO2', marker='o')
plt.scatter(df['Time'], df['VE/VCO2'], label='FECO2', marker='s')
plt.scatter(df['Time'], df['PetO2'], label='PetO2', marker='^')
plt.xlabel("Time (minutes)")
plt.ylabel("Volume (mL/min)")
plt.title("Ventilatory Equivalents & End Tidal O2 Tension over Time")
plt.legend()
plt.grid()
st.pyplot(plt)

# Plot Respiratory Exchange Ratio
plt.figure(figsize=(10, 5))
plt.scatter(df['Time'], df['RER'], label='RER', marker='o')
plt.xlabel("Time (minutes)")
plt.ylabel("RER")
plt.title("Respiratory Exchange Ratio over Time")
plt.legend()
plt.grid()
st.pyplot(plt)





