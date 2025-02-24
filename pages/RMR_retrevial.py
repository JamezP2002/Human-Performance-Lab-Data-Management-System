import pandas as pd
from pymongo import MongoClient
import streamlit as st
import matplotlib.pyplot as plt

# connecting to mongodb 
st.write("Connecting to database...")
client = MongoClient('mongodb+srv://jamesP:AaqW2WmFW9TM_KC@performance-lab.cs28l.mongodb.net/')
db = client['performance-lab']
collection = db['vo2max']
st.write("Connected to database, retrieving the data.")

# load the JSON file from the mongodb database.
document = collection.find_one() 

# Extract Tabular Data
tabular_data = document["VO2 Max Report Info"]["Tabular Data"]

# Convert to DataFrame
df = pd.DataFrame(tabular_data)
st.write(df)

# Plot VO2 and VCO2 over time
plt.figure(figsize=(10, 5))
plt.plot(df['Time'], df['VO2 STPD'], label='VO2 STPD', marker='o')
plt.plot(df['Time'], df['VCO2 STPD'], label='VCO2 STPD', marker='s')
plt.xlabel("Time (minutes)")
plt.ylabel("Volume (mL/min)")
plt.title("VO2 and VCO2 over Time")
plt.legend()
plt.grid()
plt.show()
st.pyplot(plt)