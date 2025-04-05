import pandas as pd
from pymongo import MongoClient
import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv, find_dotenv
import boto3
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, FrameBreak,
                                Paragraph, Spacer, Table, TableStyle, Image, NextPageTemplate,
                                PageBreak)
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Image as RLImage
import io

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

# Session state initialization
if 'reviewing' not in st.session_state:
    st.session_state.reviewing = False
if 'plot_index' not in st.session_state:
    st.session_state.plot_index = 0
if 'plot_comments' not in st.session_state:
    st.session_state.plot_comments = {}
if 'selected_document' not in st.session_state:
    st.session_state.selected_document = None

# Define all your plotting functions explicitly:
def plot_vslope(fig, ax):
    ax.scatter(df['VO2 STPD'], df['VCO2 STPD'], label='V-Slope', marker='o')
    ax.set_xlabel("VO2 STPD (mL/min)")
    ax.set_ylabel("VCO2 STPD (mL/min)")
    ax.set_title("V-Slope")
    ax.legend()
    ax.grid()

def plot_vo2(fig, ax):
    ax.scatter(df['Time'], df['VO2 STPD'], label='VO2 ml', marker='o')
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("VO2 STPD (mL/min)")
    ax.set_title("VO2 ml over Time")
    ax.legend()
    ax.grid()

def plot_hr(fig, ax):
    ax.scatter(df['Time'], df['HR'], label='Heart Rate', marker='o')
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Heart Rate (bpm)")
    ax.set_title("Heart Rate over Time")
    ax.legend()
    ax.grid()

def plot_fat_cho(fig, ax):
    ax.scatter(df['Time'], df['FATmin'], label='Fat Ox (g/min)', marker='o', color='tab:blue')
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Fat Oxidation (g/min)", color='tab:blue')
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax2 = ax.twinx()
    ax2.scatter(df['Time'], df['CHOmin'], label='CHO Ox (g/min)', marker='o', color='tab:orange')
    ax2.set_ylabel("CHO Oxidation (g/min)", color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    ax.set_title("Fat and CHO Oxidation over Time")
    fig.tight_layout()
    ax.grid()

def plot_vent_co2(fig, ax):
    ax.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue')
    ax.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green')
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("VE/VO2 & VE/VCO2", color='tab:blue')
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax2 = ax.twinx()
    ax2.scatter(df['Time'], df['PetCO2'], label='PetCO2', marker='o', color='tab:orange')
    ax2.set_ylabel("PetCO2", color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    ax.set_title("Ventilatory Equivalents & PetCO2 over Time")
    fig.tight_layout()
    ax.grid()

def plot_vent_o2(fig, ax):
    ax.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue')
    ax.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green')
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("VE/VO2 & VE/VCO2", color='tab:blue')
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax2 = ax.twinx()
    ax2.scatter(df['Time'], df['PetO2'], label='PetO2', marker='o', color='tab:orange')
    ax2.set_ylabel("PetO2", color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    ax.set_title("Ventilatory Equivalents & PetO2 over Time")
    fig.tight_layout()
    ax.grid()

def plot_rer(fig, ax):
    ax.scatter(df['Time'], df['RER'], label='RER', marker='o')
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("RER")
    ax.set_title("Respiratory Exchange Ratio over Time")
    ax.legend()
    ax.grid()

plot_functions = [
    ("V-Slope", plot_vslope),
    ("VO2 ml over Time", plot_vo2),
    ("Heart Rate over Time", plot_hr),
    ("Fat and CHO Ox over Time", plot_fat_cho),
    ("Ventilatory Equivalents & End Tidal CO2 Tension", plot_vent_co2),
    ("Ventilatory Equivalents & End Tidal O2 Tension", plot_vent_o2),
    ("Respiratory Exchange Ratio over Time", plot_rer),
]

# --- Main Content ---
if not st.session_state.reviewing:

    # App Title
    st.title("Report Retrieval and PDF Generation")
    st.write("Champ Human Performance Lab")

    # Dropdown for patient selection
    documents = list(collection.find())
    name_id_pairs = ["None"] + [f"{doc['VO2 Max Report Info']['Patient Info']['Name']} | {doc['_id']}" for doc in documents]
    selected_pair = st.selectbox("Choose Patient:", name_id_pairs)
    selected_name = "None" if selected_pair == "None" else selected_pair.split("|")[0].strip()

    if selected_name != "None":
        document = next(doc for doc in documents if doc["VO2 Max Report Info"]["Patient Info"]["Name"] == selected_name)
        st.session_state.selected_document = document

        patient_info = document["VO2 Max Report Info"]["Patient Info"]
        test_protocol = document["VO2 Max Report Info"]["Test Protocol"]
        results = test_protocol["Results"]
        tabular_data = document["VO2 Max Report Info"]["Tabular Data"]

        # Display patient details
        st.subheader("Patient Info")
        st.write(patient_info)

        st.subheader("Test Protocol")
        st.write(test_protocol)

        # some logic for the sport based on the exercise protocol in the test protocol
        sport = None
        if test_protocol.get("Exercise Device") == "Treadmill":
            sport = "Running"
        elif test_protocol.get("Exercise Device") == "Bike":
            sport = "Biking"
        else:
            sport = "Unknown"  # Default to Unknown if no specific protocol is matched

        # get the athlete info for the pdf report
        paitent_info_for_pdf = {
            "Name": patient_info.get("Name"),
            "Sex": patient_info.get("Sex"),
            "Age": patient_info.get("Age"),
            "Height": patient_info.get("Height"),
            "Weight": patient_info.get("Weight")
        }

        # get the test results for the pdf report
        test_results_for_pdf = {
            "Sport": sport,
            "Test Degree": test_protocol.get("Test Degree", "Unknown"),
            "Exercise Device": test_protocol.get("Exercise Device", "Unknown"),
            "Max VO2": results.get("Max VO2", "N/A"),  
            "VO2max Percentile": results.get("VO2max Percentile", "N/A")  
        }

        initial_report_context = st.text_area("Initial Report:", height=100)

        # Load DataFrame
        df = pd.DataFrame(tabular_data)
        st.session_state.df = df  
        st.session_state.athlete_data = paitent_info_for_pdf
        st.session_state.vo2_data = test_results_for_pdf
        st.session_state.initial_report_text = initial_report_context  

        if st.checkbox("Show raw tabular data"):
            st.dataframe(df)

        if st.button("Next Step: Review Plots"):
            if not initial_report_context.strip():
                st.error("Please fill in the initial report before proceeding.")
            else:
                st.session_state.reviewing = True
                st.session_state.plot_index = 0
                st.session_state.plot_comments = {}
                st.rerun()

    else:
        st.info("Please select a patient to continue.")

# --- Plot Review Section ---
if st.session_state.reviewing:

    df = st.session_state.df
    total_plots = len(plot_functions)
    plot_name, plot_func = plot_functions[st.session_state.plot_index]

    st.subheader(f"Reviewing Plot ({st.session_state.plot_index + 1}/{total_plots}): {plot_name}")

    # Create two columns for plot and comment
    plot_col, comment_col = st.columns([1, 1])

    with plot_col:
        fig, ax = plt.subplots(figsize=(7, 3.5))
        plot_func(fig, ax)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with comment_col:
        comment = st.text_area(f"Comments for '{plot_name}':",
                           key=f"comment_{st.session_state.plot_index}")
        st.session_state.plot_comments[plot_name] = comment

    col1, col2, col3 = st.columns([1,1,2])

    if st.session_state.plot_index > 0:
        if col1.button("← Back"):
            st.session_state.plot_index -= 1
            st.rerun()

    if st.session_state.plot_index < total_plots - 1:
        if col2.button("Next Plot →"):
            st.session_state.plot_index += 1
            st.rerun()
    else:
        if col2.button("✅ Generate Final PDF Report"):
            # creating a pdf report name with the name of the chosen patient
            athlete_data = st.session_state.get("athlete_data", {})
            name = athlete_data.get("Name", "Unknown")  # Get name from athlete_data session state
            pdf_path = f"test_report_{name}.pdf"  # Create PDF filename using the patient's name
            with st.spinner("Generating PDF..."):
                # Create plot images
                pdf_buffers = []
                for name, func in plot_functions:
                    fig, ax = plt.subplots(figsize=(9, 6))
                    func(fig, ax)
                    ax.set_title(f"{name}", fontsize=10)
                    plt.tight_layout()
                    buf = io.BytesIO()
                    fig.savefig(buf, format="PNG")
                    buf.seek(0)
                    pdf_buffers.append((buf, st.session_state.plot_comments.get(name, "")))
                    plt.close(fig)
        
                doc = BaseDocTemplate(pdf_path, pagesize=LETTER)
                styles = getSampleStyleSheet()
                width, height = LETTER
                header_height = 180
                body_height = height - doc.topMargin - doc.bottomMargin - header_height

                # margins for the document
                doc.topMargin = 5   
                doc.bottomMargin = 140
                doc.leftMargin = 72   
                doc.rightMargin = 72   

                header_frame = Frame(doc.leftMargin, doc.bottomMargin + body_height, doc.width, header_height, id='header')
                frame_left = Frame(doc.leftMargin, doc.bottomMargin, doc.width / 2 - 6, body_height, id='left')
                frame_right = Frame(doc.leftMargin + doc.width / 2 + 6, doc.bottomMargin, doc.width / 2 - 6, body_height, id='right')
                bottom_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, body_height, id='bottom')

                plot_height = 350  # Adjust this to how tall you want your plot
                comment_height = height - doc.topMargin - doc.bottomMargin - plot_height + 60

                plot_frame = Frame(
                    doc.leftMargin,
                    height - doc.topMargin - plot_height,
                    doc.width,
                    plot_height,
                    id='plot'
                )

                comment_frame = Frame(
                    doc.leftMargin,
                    doc.bottomMargin,
                    doc.width,
                    comment_height,
                    id='comment'
                )

                doc.addPageTemplates([
                    PageTemplate(id='ContentPage', frames=[header_frame, frame_left, frame_right, bottom_frame]),
                    PageTemplate(id='PlotPage', frames=[plot_frame, comment_frame])
                ])

                story = []

                # Logo placeholder (skip if you don't have a file)
                logo_path = "graphics/CHAMPlogo.png"
                if logo_path and os.path.exists(logo_path):
                    logo = Image(logo_path, width=100, height=100)
                    logo.hAlign = "CENTER"
                    story.append(logo)

                story.extend([
                    Paragraph("CHAMP Human Performance Lab Report", styles["Title"]),
                    Paragraph('<para align="center">Southern Connecticut State University</para>', styles["Heading2"]),
                    Spacer(1, 10),
                    FrameBreak()
                ])

                # Athlete Info
                athlete_data = st.session_state.get("athlete_data", {})
                athlete_table_data = [["Athlete Info", ""]] + [[k, str(v)] for k, v in athlete_data.items()]
                athlete_table = Table(athlete_table_data, colWidths=[100, 120])
                athlete_table.setStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ])
                story.extend([athlete_table, FrameBreak()])

                # VO2 Info
                vo2_data = st.session_state.get("vo2_data", {})
                vo2_table_data = [["Test Results", ""]] + [[k, str(v)] for k, v in vo2_data.items()]
                vo2_table = Table(vo2_table_data, colWidths=[100, 150])
                vo2_table.setStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ])
                story.append(vo2_table)
                story.append(FrameBreak())
                story.append(Spacer(1, 110))

                initial_report_text = st.session_state.get("initial_report_text", "")
                #print("initial_report_text = ", repr(initial_report_text)) # debug
                story.extend([
                    Paragraph("<b>Summary Report:</b>", styles["Heading3"]),
                    Spacer(1, 10),
                    Paragraph(initial_report_text or "No report provided.", styles["Normal"]),
                    Spacer(1, 20),
                ])

                story.append(NextPageTemplate('PlotPage'))
                story.append(PageBreak())

                # Plots and comments
                for buf, comment in pdf_buffers:
                    img = Image(buf, width=500, height=300)
                    img.hAlign = "CENTER"
                    story.append(img)
                    story.append(FrameBreak())
                    story.append(Paragraph(f"<b>Analysis:</b>", styles["Heading3"]))
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(f"{comment}", styles["Normal"]))
                    story.append(Spacer(1, 10))
                    if logo_path and os.path.exists(logo_path):
                        logo = Image(logo_path, width=100, height=100)
                        logo.hAlign = "RIGHT"
                    story.append(logo)
                    story.append(PageBreak())

                doc.build(story)
                st.success("✅ PDF generated successfully!")

                # Define file and bucket
                file_name = pdf_path
                bucket_name = "champ-hpl-bucket"
                s3_key = f'reports/{pdf_path}'

                # asking user if they want to save the plots to s3
                st.write("Saving plots to S3 bucket...")
                s3_client.upload_file(file_name, bucket_name, s3_key)
                st.write("Plots saved to S3 bucket.")
                st.write("Done.")

                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name=pdf_path)

                st.session_state.reviewing = False

    if col3.button("Return to Patient Selection"):
        st.session_state.reviewing = False
        st.session_state.plot_index = 0
        st.session_state.plot_comments = {}
        st.rerun()

    # Define file and bucket
    #file_name = pdf_path
    #bucket_name = "champ-hpl-bucket"
    #s3_key = f'reports/{pdf_path}'

    # asking user if they want to save the plots to s3
    #st.write("Do you want to save the plots to S3 bucket?")
    #if st.button("Save Plots to S3"):
    #    st.write("Saving plots to S3 bucket...")
    #    s3_client.upload_file(file_name, bucket_name, s3_key)
    #    st.write("Plots saved to S3 bucket.")
    #    st.write("Done.")

    # store the plots created into a s3 bucket
    #st.write("Saving plots to S3 bucket...")
    #s3_client.upload_file(file_name, bucket_name, s3_key)
    #st.write("Plots saved to S3 bucket.")
    #st.write("Done.")

