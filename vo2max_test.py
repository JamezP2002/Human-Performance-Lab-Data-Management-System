import pandas as pd
from pymongo import MongoClient
import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv, find_dotenv
import boto3
import io
import numpy as np

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
    
    def get_paitent(self):
        pass

    def select_patient(self):
        """Displays patient dropdown and returns selected patient name and ID."""
        documents = list(self.collection.find())
        name_id_pairs = ["None"] + [
            f"{doc['VO2 Max Report Info']['Patient Info']['Name']} | {doc['_id']}"
            for doc in documents
        ]
        selected_pair = st.selectbox("Choose Patient:", name_id_pairs)
        selected_name = "None" if selected_pair == "None" else selected_pair.split("|")[0].strip()

        if selected_name != "None":
            document = next(doc for doc in documents if doc["VO2 Max Report Info"]["Patient Info"]["Name"] == selected_name)
            st.session_state.selected_document = document

            patient_info = document["VO2 Max Report Info"]["Patient Info"]
            test_protocol = document["VO2 Max Report Info"]["Test Protocol"]
            results = test_protocol["Results"]
            tabular_data = document["VO2 Max Report Info"]["Tabular Data"]
            df = pd.DataFrame(tabular_data)

            # converting from l to ml
            columns_to_convert = ['VO2 STPD', 'VCO2 STPD']
            df[columns_to_convert] = df[columns_to_convert] * 1000

            st.session_state.df = df

            return patient_info, test_protocol, results, df
        else:
            st.info("Please select a patient to continue.")
            return selected_name
        
    def get_plot_functions(self):
        df = st.session_state.get("df")

        def plot_vslope(ax, df):
            # Original scatter plot
            ax.scatter(df['VO2 STPD'], df['VCO2 STPD'], label='V-Slope', marker='o')
            
            # Sort data by VO2
            sorted_data = df.sort_values('VO2 STPD')
            vo2_values = sorted_data['VO2 STPD'].values
            vco2_values = sorted_data['VCO2 STPD'].values
            
            # Find the approximate threshold point
            mid_point = len(vo2_values) // 2
            
            # Fit lines before and after threshold
            z1 = np.polyfit(vo2_values[:mid_point], vco2_values[:mid_point], 1)
            p1 = np.poly1d(z1)
            
            z2 = np.polyfit(vo2_values[mid_point:], vco2_values[mid_point:], 1)
            p2 = np.poly1d(z2)
            
            # Find intersection point by solving p1(x) = p2(x)
            a, b = z1
            c, d = z2
            intersection_x = (d-b)/(a-c)
            intersection_y = p1(intersection_x)
            
            # Plot trend lines up to intersection point
            x_range1 = np.linspace(vo2_values.min(), vo2_values.max() - 900, 50)
            x_range2 = np.linspace(vo2_values.min() + 700, vo2_values.max(), 50)
            ax.plot(x_range1, p1(x_range1), '--', color='green', label='Pre-threshold')
            ax.plot(x_range2, p2(x_range2), '--', color='red', label='Post-threshold')
            
            # Add vertical line at intersection
            ax.axvline(x=intersection_x, color='blue', linestyle=':', label='Threshold')
            
            ax.set_xlabel("VO2 STPD (mL/min)")
            ax.set_ylabel("VCO2 STPD (mL/min)")
            ax.set_title("V-Slope")
            ax.legend()
            ax.grid()

        def plot_vo2(ax, df):
            # Original scatter plot
            ax.scatter(df['Time'], df['VO2 STPD'], label='VO2 ml', marker='o')
            
            # Add polynomial trendline
            z = np.polyfit(df['Time'], df['VO2 STPD'], 3)
            p = np.poly1d(z)
            x_trend = np.linspace(df['Time'].min(), df['Time'].max(), 100)
            ax.plot(x_trend, p(x_trend), '--', color='tab:red', label='VO2 Trend')
            
            ax.set_xlabel("Time (minutes)")
            ax.set_ylabel("VO2 STPD (mL/min)")
            ax.set_title("VO2 ml over Time")
            ax.legend()
            ax.grid()

        def plot_hr(ax, df):
            ax.scatter(df['Time'], df['HR'], label='Heart Rate', marker='o')
            ax.set_xlabel("Time (minutes)")
            ax.set_ylabel("Heart Rate (bpm)")
            ax.set_title("Heart Rate over Time")
            ax.legend()
            ax.grid()

        def plot_fat_cho(ax, df):
            # Original scatter plots
            ax.scatter(df['Time'], df['FATmin'], label='Fat Ox (g/min)', marker='o', color='tab:blue')
            ax.set_xlabel("Time (minutes)")
            ax.set_ylabel("Fat Oxidation (g/min)", color='tab:blue')
            ax.tick_params(axis='y', labelcolor='tab:blue')
            
            # Add polynomial trendline for fat oxidation
            z = np.polyfit(df['Time'], df['FATmin'], 3)
            p = np.poly1d(z)
            x_trend = np.linspace(df['Time'].min(), df['Time'].max(), 100)
            ax.plot(x_trend, p(x_trend), '--', color='tab:blue', label='Fat Ox Trend')
            
            # CHO plot on secondary axis
            ax2 = ax.twinx()
            ax2.scatter(df['Time'], df['CHOmin'], label='CHO Ox (g/min)', marker='o', color='tab:orange')
            ax2.set_ylabel("CHO Oxidation (g/min)", color='tab:orange')
            ax2.tick_params(axis='y', labelcolor='tab:orange')
            
            ax.set_title("Fat and CHO Oxidation over Time")
            ax.grid()

        def plot_vent_co2(ax, df):
            ax.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue')
            ax.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green')
            ax.set_xlabel("Time (minutes)")
            ax.set_ylabel("VE/VO2 & VE/VCO2", color='tab:blue')
            ax.tick_params(axis='y', labelcolor='tab:blue')
            ax2 = ax.twinx()
            ax2.scatter(df['Time'], df['PetCO2'], label='PetCO2', marker='o', color='tab:orange')
            # Add polynomial trendline for PetCO2
            z = np.polyfit(df['Time'], df['PetCO2'], 3)
            p = np.poly1d(z)
            x_trend = np.linspace(df['Time'].min(), df['Time'].max(), 100)
            ax2.plot(x_trend, p(x_trend), '--', color='tab:orange', label='PetCO2 Trend')
            
            ax2.set_ylabel("PetCO2", color='tab:orange')
            ax2.tick_params(axis='y', labelcolor='tab:orange')
            ax.set_title("Ventilatory Equivalents & PetCO2 over Time")
            
            # Combine legends from both axes
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, loc='best')
            ax.grid()

        def plot_vent_o2(ax, df):
            ax.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue')
            ax.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green')
            ax.set_xlabel("Time (minutes)")
            ax.set_ylabel("VE/VO2 & VE/VCO2", color='tab:blue')
            ax.tick_params(axis='y', labelcolor='tab:blue')
            ax2 = ax.twinx()
            ax2.scatter(df['Time'], df['PetO2'], label='PetO2', marker='o', color='tab:orange')
            # Add polynomial trendline for PetO2
            z = np.polyfit(df['Time'], df['PetO2'], 3)
            p = np.poly1d(z)
            x_trend = np.linspace(df['Time'].min(), df['Time'].max(), 100)
            ax2.plot(x_trend, p(x_trend), '--', color='tab:orange', label='PetO2 Trend')
            ax2.set_ylabel("PetO2", color='tab:orange')
            ax2.tick_params(axis='y', labelcolor='tab:orange')
            ax.set_title("Ventilatory Equivalents & PetO2 over Time")
            
            # Combine legends from both axes
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, loc='best')
            ax.grid()

        def plot_rer(ax, df):
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

        return plot_functions
    
    def create_plots(self):
        df = st.session_state.get("df")

        plot_functions = self.get_plot_functions()
        fig, axs = plt.subplots(4, 2, figsize=(20, 24))
        axs = axs.flatten()

        for i, (title, func) in enumerate(plot_functions):
            ax = axs[i]
            func(ax, df)
            ax.set_title(title)

        st.pyplot(fig)

    def plot_single_figure(self, index):
        df = st.session_state.get("df")
        plot_functions = self.get_plot_functions()
        title, func = plot_functions[index]
        fig, ax = plt.subplots(figsize=(8, 5))
        func(ax, df)
        st.subheader(title)
        st.pyplot(fig)

    def review_report(self):
        df = st.session_state.get("df")

        if 'plot_index' not in st.session_state:
            st.session_state.plot_index = 0

        if 'plot_comments' not in st.session_state: 
            st.session_state.plot_comments = {}

        plot_functions = self.get_plot_functions()
        total_plots = len(plot_functions)

        st.subheader(f"Reviewing Plot ({st.session_state.plot_index + 1}/{total_plots})")

        col1, col2 = st.columns([1, 1])
        with col1:
            self.plot_single_figure(st.session_state.plot_index)

        with col2:
            plot_name, _ = plot_functions[st.session_state.plot_index]
            comment = st.text_area(f"Comments for '{plot_name}':", key=f"comment_{st.session_state.plot_index}")
            st.session_state.plot_comments[plot_name] = comment

        c1, c2 = st.columns([1, 1])

        if st.session_state.plot_index > 0 and c1.button("← Back"):
            st.session_state.plot_index -= 1
            st.rerun()

        if st.session_state.plot_index < total_plots - 1:
            if c2.button("Next Plot →"):
                st.session_state.plot_index += 1
                st.rerun()
        else:
            if c2.button("✅ Generate Final PDF Report"):
                self.generate_pdf()

    def generate_pdf(self, patient_info, test_protocol, results):
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

