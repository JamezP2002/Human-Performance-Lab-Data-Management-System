import pandas as pd
from pymongo import MongoClient
import streamlit as st

# connecting to mongodb 
st.write("Connecting to database...")
client = MongoClient('mongodb+srv://jamesP:AaqW2WmFW9TM_KC@performance-lab.cs28l.mongodb.net/')
db = client['performance-lab']
collection = db['rmr']
st.write("Connected to database, retrieving the data.")

# load the JSON file from the mongodb database.
documents = collection.find({"Tabular Data": {"$exists": True}})  
for document in documents:
    st.write(document["tabular_data"]) 