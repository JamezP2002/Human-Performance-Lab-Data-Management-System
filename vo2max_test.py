import pandas as pd
from pymongo import MongoClient
import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv, find_dotenv
import boto3
import io

class VO2MaxTest:
    def __init__(self, user_id=None):
        self.user_id = user_id

        # Load .env and connect to DB
        dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
        load_dotenv(dotenv_path)

        database_credentials = os.getenv("database_credentials")
        self.client = MongoClient(database_credentials)
        self.db = self.client['performance-lab']
        self.collection = self.db['vo2max']

    def select_patient(self):
        """Displays patient dropdown and returns selected patient name and ID."""
        documents = list(self.collection.find())
        name_id_pairs = ["None"] + [
            f"{doc['VO2 Max Report Info']['Patient Info']['Name']} | {doc['_id']}"
            for doc in documents
        ]
        selected_pair = st.selectbox("Choose Patient:", name_id_pairs)

        if selected_pair == "None":
            return None, None

        selected_name, selected_id = selected_pair.split("|")
        return selected_name.strip(), selected_id.strip()
    
    def 

