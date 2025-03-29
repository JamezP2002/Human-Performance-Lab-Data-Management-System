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
from io import BytesIO

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

# creating a header for the app
st.html(
    f"""
    <div style="display: flex; 'text-align: center;' align-items: center; justify-content: center; margin-bottom: 20px;">
        <!-- Right side: title and subtitle -->
        <div>
            <h1 style="margin-bottom: 0; font-size: 50px">Report Retrieval and PDF Generation</h1>
            <p style="text-align: center; margin-top: 0; font-size: 18px;">
                Champ Human Performance Lab
            </p>
        </div>
    </div>
    """
)

st.html(
    "<div style='text-align: center;'>"
    "This is the report creator. It searches the MongoDB database for the user you're looking for, "
    "then creates a report for you to export as a PDF, with optional minor adjustments if needed."
    "</div>"
)

# create a dropdown menu for the patient name to select the document to load
documents = list(collection.find())
patient_names = ["None"] + [doc["VO2 Max Report Info"]["Patient Info"]["Name"] for doc in documents]
selected_name = st.selectbox("Choose:", patient_names)

if selected_name != "None":
    document = next(doc for doc in documents if doc["VO2 Max Report Info"]["Patient Info"]["Name"] == selected_name)

#####################################################
# Extracting Section
#####################################################

    # Extract and save Patient Info into variables
    patient_info = document["VO2 Max Report Info"]["Patient Info"]
    patient_name = patient_info['Name']
    patient_age = patient_info['Age']
    patient_height = patient_info['Height']
    patient_weight = patient_info['Weight']

    # Display Patient Info
    st.write("Patient Info:")
    st.write(f"Name: {patient_name}")
    st.write(f"Age: {patient_age}")
    st.write(f"Height: {patient_height}")
    st.write(f"Weight: {patient_weight}")
    st.write("")

    # Extract and save Test Info into variables
    test_protocol = document["VO2 Max Report Info"]["Test Protocol"]
    test_degree = test_protocol['Test Degree']
    exercise_device = test_protocol['Exercise Device']

    # Determine Sport based on Exercise Device
    if exercise_device == "Treadmill":
        sport = "Running"
    else:
        sport = "Biking"

    # Display Test Info
    st.write("Test Protocol:")
    st.write(f"Test Degree: {test_degree}")
    st.write(f"Exercise Device: {exercise_device}")
    st.write("")

    # Display Test results
    results = document["VO2 Max Report Info"]["Test Protocol"]["Results"]
    maxVO2 = results['Max VO2']
    vo2max_percentile = results['VO2max Percentile']

    st.write("Test Results:")
    st.write(f"Max VO2: {maxVO2} mL/kg/min")
    st.write(f"VO2max Percentile: {vo2max_percentile}")

    # create dictonary of athlete data
    athlete_data = {
        "Name": patient_name,
        "Age": patient_age,
        "Height": patient_height,
        "Weight": patient_weight,
        "Sport": sport,
        "Test Degree": test_degree,
        "Exercise Device": exercise_device,
        }
    
    # create dictonary of test results
    vo2_data = {
        "VO2 Max: (Relative)": maxVO2,
        "VO2 Max Percentile": vo2max_percentile,
    }

    # Extract Tabular Data
    tabular_data = document["VO2 Max Report Info"]["Tabular Data"]

    # Convert to DataFrame (allow it to be hidden)
    df = pd.DataFrame(tabular_data)
    
    # asking user to put in their report text based on the given data
    report_text = st.text_area("Inital Report:", height=100)

    if st.checkbox("Show raw tabular data"):
        st.dataframe(df)

    if st.button("Generate PDF Report"):
        if not report_text.strip():
            st.error("Please fill in the report text box before generating the PDF.")
        else:
            #####################################################
            # PDF Generation Section
            #####################################################

            pdf_buffers = []
            # A helper function that creates a plot, saves it to a BytesIO buffer, displays it in Streamlit, and returns the buffer.
            def generate_and_show_plot(plot_func):
                fig, ax = plt.subplots(figsize=(10, 5))
                plot_func(fig, ax)
                buf = BytesIO()
                fig.savefig(buf, format="PNG", bbox_inches="tight")
                buf.seek(0)
                st.pyplot(fig)  # Display the plot in Streamlit
                plt.close(fig)
                return buf

            col1, col2 = st.columns(2)

            # Plot 1: V-Slope in col1
            with col1:
                def plot_vslope(fig, ax):
                    ax.scatter(df['VO2 STPD'], df['VCO2 STPD'], label='V-Slope', marker='o')
                    ax.set_xlabel("VO2 STPD (mL/min)")
                    ax.set_ylabel("VCO2 STPD (mL/min)")
                    ax.set_title("V-Slope")
                    ax.legend()
                    ax.grid()
                buf1 = generate_and_show_plot(plot_vslope)
                pdf_buffers.append(buf1)

            # Plot 2: VO2 ml over Time in col2
            with col2:
                def plot_vo2(fig, ax):
                    ax.scatter(df['Time'], df['VO2 STPD'], label='VO2 ml', marker='o')
                    ax.set_xlabel("Time (minutes)")
                    ax.set_ylabel("Volume (mL/min)")
                    ax.set_title("VO2 ml over Time")
                    ax.legend()
                    ax.grid()
                buf2 = generate_and_show_plot(plot_vo2)
                pdf_buffers.append(buf2)

            # Plot 3: HR Scatter in col1
            with col1:
                def plot_hr(fig, ax):
                    ax.scatter(df['Time'], df['HR'], label='HR', marker='o')
                    ax.set_xlabel("Time (minutes)")
                    ax.set_ylabel("Heart Rate (bpm)")
                    ax.set_title("Heart Rate over Time")
                    ax.legend()
                    ax.grid()
                buf3 = generate_and_show_plot(plot_hr)
                pdf_buffers.append(buf3)

            # Plot 4: Fat and CHO Ox in col2 (with twin axes)
            with col2:
                def plot_fat_cho(fig, ax):
                    ax.set_xlabel("Time (minutes)")
                    ax.set_ylabel("Fat Oxidation Rate (g/min)", color='tab:blue')
                    ax.scatter(df['Time'], df['FATmin'], label='Fat Ox', marker='o', color='tab:blue')
                    ax.tick_params(axis='y', labelcolor='tab:blue')
                    ax2 = ax.twinx()
                    ax2.set_ylabel("CHO Oxidation Rate (g/min)", color='tab:orange')
                    ax2.scatter(df['Time'], df['CHOmin'], label='CHO Ox', marker='o', color='tab:orange')
                    ax2.tick_params(axis='y', labelcolor='tab:orange')
                    fig.suptitle("Fat and CHO Ox over Time")
                    fig.tight_layout()
                    ax.grid()
                buf4 = generate_and_show_plot(plot_fat_cho)
                pdf_buffers.append(buf4)

            # Plot 5: Ventilatory Equivalents & End Tidal CO2 Tension in col1 (with twin axes)
            with col1:
                def plot_vent_co2(fig, ax):
                    ax.set_xlabel("Time (minutes)")
                    ax.set_ylabel("VE/VO2 & VE/VCO2", color='tab:blue')
                    ax.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue')
                    ax.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green')
                    ax.tick_params(axis='y', labelcolor='tab:blue')
                    ax2 = ax.twinx()
                    ax2.set_ylabel("PetCO2", color='tab:orange')
                    ax2.scatter(df['Time'], df['PetCO2'], label='PetCO2', marker='o', color='tab:orange')
                    ax2.tick_params(axis='y', labelcolor='tab:orange')
                    fig.suptitle("Ventilatory Equivalents & End Tidal CO2 Tension over Time")
                    fig.tight_layout()
                    ax.grid()
                buf5 = generate_and_show_plot(plot_vent_co2)
                pdf_buffers.append(buf5)

            # Plot 6: Ventilatory Equivalents & End Tidal O2 Tension in col2 (with twin axes)
            with col2:
                def plot_vent_o2(fig, ax):
                    ax.set_xlabel("Time (minutes)")
                    ax.set_ylabel("VE/VO2 & VE/VCO2", color='tab:blue')
                    ax.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue')
                    ax.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green')
                    ax.tick_params(axis='y', labelcolor='tab:blue')
                    ax2 = ax.twinx()
                    ax2.set_ylabel("PetO2", color='tab:orange')
                    ax2.scatter(df['Time'], df['PetO2'], label='PetO2', marker='o', color='tab:orange')
                    ax2.tick_params(axis='y', labelcolor='tab:orange')
                    fig.suptitle("Ventilatory Equivalents & End Tidal O2 Tension over Time")
                    fig.tight_layout()
                    ax.grid()
                buf6 = generate_and_show_plot(plot_vent_o2)
                pdf_buffers.append(buf6)

            # Plot 7: Respiratory Exchange Ratio in col1
            with col1:
                def plot_rer(fig, ax):
                    ax.scatter(df['Time'], df['RER'], label='RER', marker='o')
                    ax.set_xlabel("Time (minutes)")
                    ax.set_ylabel("RER")
                    ax.set_title("Respiratory Exchange Ratio over Time")
                    ax.legend()
                    ax.grid()
                buf7 = generate_and_show_plot(plot_rer)
                pdf_buffers.append(buf7)

            # Adjust the width/height as needed.
            rl_images = [Image(buf, width=300, height=150) for buf in pdf_buffers]

            doc = BaseDocTemplate("sample_report.pdf", pagesize=LETTER)
            styles = getSampleStyleSheet()
            width, height = LETTER

            # First page template: header plus two columns (left/right)
            header_height = 180  # height for header content
            body_height = height - doc.topMargin - doc.bottomMargin - header_height

            header_frame = Frame(doc.leftMargin, doc.bottomMargin + body_height,
                                doc.width, header_height, id='header')
            frame_left = Frame(doc.leftMargin, doc.bottomMargin,
                            doc.width/2 - 6, body_height, id='left')
            frame_right = Frame(doc.leftMargin + doc.width/2 + 6, doc.bottomMargin,
                                doc.width/2 - 6, body_height, id='right')
            bottom_frame = Frame(doc.leftMargin, doc.bottomMargin,
                            doc.width, body_height, id='bottom')

            # Second page template: a single full-page frame for plots
            plot_frame = Frame(doc.leftMargin, doc.bottomMargin,
                            doc.width, height - doc.topMargin - doc.bottomMargin, id='plot')

            # Add both templates to the document
            doc.addPageTemplates([
                PageTemplate(id='ContentPage', frames=[header_frame, frame_left, frame_right, bottom_frame]),
                PageTemplate(id='PlotPage', frames=[plot_frame])
            ])

            story = []

            # Header Content: Logo, Title, Subtitle
            logo_path = "graphics/CHAMPlogo.png"  # update as needed
            if logo_path and os.path.exists(logo_path):
                logo = Image(logo_path, width=100, height=100)
                logo.hAlign = "LEFT"
                story.append(logo)

            title = Paragraph("CHAMP Human Performance Lab", styles["Title"])
            story.append(title)
            subtitle = Paragraph('<para align="center">Southern Connecticut State University</para>', styles["Heading2"])
            story.append(subtitle)
            story.append(Spacer(1, 10))
            story.append(FrameBreak())

            # Athlete Info Table in Left Column
            athlete_table_data = [["Athlete Info", ""]]
            for k, v in athlete_data.items():
                athlete_table_data.append([k, str(v)])
                if k == "Sport":
                    athlete_table_data.append(["", ""])
            athlete_table = Table(athlete_table_data, colWidths=[100, 120])
            athlete_table.setStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
            story.append(athlete_table)
            story.append(FrameBreak())

            # VO2 Data Table in Right Column
            vo2_table_data = [["Test Results", ""]]
            for k, v in vo2_data.items():
                vo2_table_data.append([k, str(v)])
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
            story.append(Spacer(1, 190))

            # add a text section where the user can type in the report
            report_paragraph = Paragraph(report_text, styles["Normal"])
            story.append(report_paragraph)

            # Add vertical spacing before switching to plot page
            story.append(Spacer(1, 50))

            # Tell ReportLab to use the new page template for subsequent content.
            story.append(NextPageTemplate('PlotPage'))
            story.append(PageBreak())

            for i, img in enumerate(rl_images):
                story.append(img)
                img.hAlign = "LEFT" 
                story.append(Spacer(1, 10))  # adjust spacing as needed

            doc.build(story)
            print("PDF report generated successfully.")
            st.success("PDF report generated successfully.")

    # Define file and bucket
    #file_name = pdf_path
    #bucket_name = "champ-hpl-bucket"
    #s3_key = f'plots/{pdf_path}'

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

else:
    st.write("Please select a patient to load.")

