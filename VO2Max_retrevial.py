import pandas as pd
from pymongo import MongoClient
import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv, find_dotenv
import boto3
from matplotlib.backends.backend_pdf import PdfPages

# find and load the .env file
dotenv_path = os.path.abspath(os.path.join("capstone work/.env"))
#print(dotenv_path)  # Debugging
load_dotenv(dotenv_path)

# load the environment variables
database_credentials = os.getenv("database_credentials")
aws_access_key_id = os.getenv("aws_access_key_id")
aws_secret_access_key = os.getenv("aws_secret_access_key")

# connecting to s3 bucket
s3_client = boto3.client('s3',
                          aws_access_key_id=aws_access_key_id, 
                          aws_secret_access_key=aws_secret_access_key,
                          region_name='us-east-1'
                          )

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

# Extract Tabular Data
tabular_data = document["VO2 Max Report Info"]["Tabular Data"]

# Convert to DataFrame (allow it to be hidden)
df = pd.DataFrame(tabular_data)
if st.checkbox("Show raw tabular data"):
    st.dataframe(df)

# Create columns for better layout
col1, col2 = st.columns(2)

# Create a PdfPages object to save the plots
pdf_path = f"{selected_name}_VO2Max_Plots.pdf"
pdf_pages = PdfPages(pdf_path)

# Plot V-Slope
with col1:
    plt.figure(figsize=(10, 5))
    plt.scatter(df['VO2 STPD'], df['VCO2 STPD'], label='V-Slope', marker='o')
    plt.xlabel("VO2 STPD (mL/min)")
    plt.ylabel("VCO2 STPD (mL/min)")
    plt.title("V-Slope")
    plt.legend()
    plt.grid()
    st.pyplot(plt)
    pdf_pages.savefig()  # Save the figure to the PDF

# Plot VO2 ml
with col2:
    plt.figure(figsize=(10, 5))
    plt.scatter(df['Time'], df['VO2 STPD'], label='VO2 ml', marker='o')
    plt.xlabel("Time (minutes)")
    plt.ylabel("Volume (mL/min)")
    plt.title("VO2 ml over Time")
    plt.legend()
    plt.grid()
    st.pyplot(plt)
    pdf_pages.savefig()  # Save the figure to the PDF

# Plot HR scatter
with col1:
    plt.figure(figsize=(10, 5))
    plt.scatter(df['Time'], df['HR'], label='HR', marker='o')
    plt.xlabel("Time (minutes)")
    plt.ylabel("Heart Rate (bpm)")
    plt.title("Heart Rate over Time")
    plt.legend()
    plt.grid()
    st.pyplot(plt)
    pdf_pages.savefig()  # Save the figure to the PDF

# Plot Fat and CHO Ox
with col2:
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.set_xlabel("Time (minutes)")
    ax1.set_ylabel("Fat Oxidation Rate (g/min)", color='tab:blue')
    ax1.scatter(df['Time'], df['FATmin'], label='Fat Ox', marker='o', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax2 = ax1.twinx()
    ax2.set_ylabel("CHO Oxidation Rate (g/min)", color='tab:orange')
    ax2.scatter(df['Time'], df['CHOmin'], label='CHO Ox', marker='o', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    fig.suptitle("Fat and CHO Ox over Time")
    fig.tight_layout()
    ax1.grid()
    st.pyplot(fig)
    pdf_pages.savefig(fig)  # Save the figure to the PDF

# Plot Ventilatory Equivalents & End Tidal CO2 Tension
with col1:
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.set_xlabel("Time (minutes)")
    ax1.set_ylabel("VE/VO2 & VE/VCO2", color='tab:blue')
    ax1.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue')
    ax1.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax2 = ax1.twinx()
    ax2.set_ylabel("PetCO2", color='tab:orange')
    ax2.scatter(df['Time'], df['PetCO2'], label='PetCO2', marker='o', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    fig.suptitle("Ventilatory Equivalents & End Tidal CO2 Tension over Time")
    fig.tight_layout()
    ax1.grid()
    st.pyplot(fig)
    pdf_pages.savefig(fig)  # Save the figure to the PDF

# Plot Ventilatory Equivalents & End Tidal O2 Tension
with col2:
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.set_xlabel("Time (minutes)")
    ax1.set_ylabel("VE/VO2 & VE/VCO2", color='tab:blue')
    ax1.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue')
    ax1.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax2 = ax1.twinx()
    ax2.set_ylabel("PetO2", color='tab:orange')
    ax2.scatter(df['Time'], df['PetO2'], label='PetO2', marker='o', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    fig.suptitle("Ventilatory Equivalents & End Tidal O2 Tension over Time")
    fig.tight_layout()
    ax1.grid()
    st.pyplot(fig)
    pdf_pages.savefig(fig)  # Save the figure to the PDF

# Plot Respiratory Exchange Ratio
with col1:
    plt.figure(figsize=(10, 5))
    plt.scatter(df['Time'], df['RER'], label='RER', marker='o')
    plt.xlabel("Time (minutes)")
    plt.ylabel("RER")
    plt.title("Respiratory Exchange Ratio over Time")
    plt.legend()
    plt.grid()
    st.pyplot(plt)
    pdf_pages.savefig()  # Save the figure to the PDF

# Close the PdfPages object
pdf_pages.close()

# Define file and bucket
file_name = pdf_path
bucket_name = "champ-hpl-bucket"
s3_key = f'plots/{pdf_path}'

# asking user if they want to save the plots to s3
st.write("Do you want to save the plots to S3 bucket?")
if st.button("Save Plots to S3"):
    st.write("Saving plots to S3 bucket...")
    s3_client.upload_file(file_name, bucket_name, s3_key)
    st.write("Plots saved to S3 bucket.")
    st.write("Done.")

# store the plots created into a s3 bucket
#st.write("Saving plots to S3 bucket...")
#s3_client.upload_file(file_name, bucket_name, s3_key)
#st.write("Plots saved to S3 bucket.")
#st.write("Done.")


