import pandas as pd
from pymongo import MongoClient
import streamlit as st

# connecting to mongodb 
client = MongoClient('mongodb://localhost:27017/')
db = client['perfomanceLab']
collection = db['vo2max']

# Load the Excel file and do a test set (just paitent infomation)
uploaded_file = st.file_uploader("Choose a file")
df = pd.read_excel(uploaded_file, header=None)

st.write("Original File:")
st.write(df)

###########################################################################################
# Unstructured Data #
###########################################################################################