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
import numpy as np
from datetime import datetime

class VO2MaxTest:
    def __init__(self, user_id=None):
        """Initialize database connection, S3 client, and prepare environment."""
        self.user_id = user_id

        # Load environment variables (.env)
        load_dotenv()

        # Setup MongoDB connection
        database_credentials = os.getenv("database_credentials")
        self.client = MongoClient(database_credentials)
        self.db = self.client['performance-lab']
        self.collection = self.db['tests']  
        self.users_col = self.db['users']
        self.reports_col = self.db['reports']

        # Setup AWS S3 connection for storing PDFs
        aws_access_key_id = os.getenv("aws_access_key_id")
        aws_secret_access_key = os.getenv("aws_secret_access_key")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name='us-east-1'
        )

    def parse_test(self, document):
        """Parse the provided VO2 Max document and load it into Streamlit session."""
        try:
            # Save entire document to session
            st.session_state.selected_document = document

            # Break apart key data sections
            report_info = document["VO2 Max Report Info"]
            client_info = report_info["Client Info"]
            test_protocol = report_info["Test Protocol"]
            results = test_protocol["Results"]
            tabular_data = report_info["Tabular Data"]

            # Convert tabular data into dataframe for easy use
            df = pd.DataFrame(tabular_data)

            # Rescale VO2 and VCO2 to mL (stored as L originally)
            columns_to_convert = ['VO2 STPD', 'VCO2 STPD']
            df[columns_to_convert] = df[columns_to_convert] * 1000

            # Store DataFrame in session
            st.session_state.df = df

            return client_info, test_protocol, results, df

        except Exception as e:
            st.error(f"Failed to parse test document: {e}")
            return None
        
    def get_plot_functions(self):
        """Return list of plotting functions for different VO2 Max test metrics."""
        df = st.session_state.get("df")

        # --- Plot: V-Slope Analysis ---
        def plot_vslope(ax, df):
            """Plot V-Slope (VO2 vs VCO2) and determine ventilatory threshold."""
            ax.scatter(df['VO2 STPD'], df['VCO2 STPD'], label='V-Slope', marker='o', s=10)

            # Sort data to fit two linear trends
            sorted_data = df.sort_values('VO2 STPD')
            vo2_values = sorted_data['VO2 STPD'].values
            vco2_values = sorted_data['VCO2 STPD'].values
            mid_point = len(vo2_values) // 2

            # Fit trendlines before and after midpoint
            z1 = np.polyfit(vo2_values[:mid_point], vco2_values[:mid_point], 1)
            p1 = np.poly1d(z1)

            z2 = np.polyfit(vo2_values[mid_point:], vco2_values[mid_point:], 1)
            p2 = np.poly1d(z2)

            # Find intersection (threshold)
            a, b = z1
            c, d = z2
            intersection_x = (d - b) / (a - c)
            intersection_y = p1(intersection_x)

            # Create separate line ranges before/after threshold
            x_range1 = np.linspace(vo2_values.min(), vo2_values.max() - 700, 50)
            x_range2 = np.linspace(vo2_values.min() + 1100, vo2_values.max(), 50)

            ax.plot(x_range1, p1(x_range1), '--', color='green', label='Pre-threshold')
            ax.plot(x_range2, p2(x_range2), '--', color='red', label='Post-threshold')
            ax.axvline(x=intersection_x, color='blue', linestyle=':', label='Threshold')

            # Formatting
            ax.set_xlabel("VO2 STPD (mL/min)", fontweight='bold')
            ax.set_ylabel("VCO2 STPD (mL/min)", fontweight='bold')
            ax.set_title("V-Slope", fontweight='bold')
            ax.legend(fontsize=8)
            ax.grid()

        # --- Plot: VO2 Over Time ---
        def plot_vo2(ax, df):
            """Plot VO2 uptake over time with a smoothed trendline."""
            ax.scatter(df['Time'], df['VO2 STPD'], label='VO2 ml', marker='o', s=10)

            # Trendline (3rd degree polynomial)
            z = np.polyfit(df['Time'], df['VO2 STPD'], 3)
            p = np.poly1d(z)
            x_trend = np.linspace(df['Time'].min(), df['Time'].max(), 100)
            ax.plot(x_trend, p(x_trend), '--', color='blue', label='VO2 Trend')

            ax.set_xlabel("Time (minutes)", fontweight='bold')
            ax.set_ylabel("VO2 STPD (mL/min)", fontweight='bold')
            ax.set_title("VO2 ml over Time", fontweight='bold')
            ax.legend(fontsize=8)
            ax.grid()

        # --- Plot: Heart Rate ---
        def plot_hr(ax, df):
            """Plot Heart Rate over time."""
            ax.scatter(df['Time'], df['HR'], label='Heart Rate', marker='o', s=10)

            ax.set_xlabel("Time (minutes)", fontweight='bold')
            ax.set_ylabel("Heart Rate (bpm)", fontweight='bold')
            ax.set_title("Heart Rate over Time", fontweight='bold')
            ax.legend(fontsize=8)
            ax.grid()

        # --- Plot: Fat and Carbohydrate Oxidation ---
        def plot_fat_cho(ax, df):
            """Plot fat and carbohydrate (CHO) oxidation rates over time."""
            ax.scatter(df['Time'], df['FATmin'], label='Fat Ox (g/min)', marker='o', color='tab:blue', s=10)
            
            # Fat Oxidation trendline
            z = np.polyfit(df['Time'], df['FATmin'], 3)
            p = np.poly1d(z)
            x_trend = np.linspace(df['Time'].min(), df['Time'].max(), 100)
            ax.plot(x_trend, p(x_trend), '--', color='blue', label='Fat Ox Trend')

            ax.set_xlabel("Time (minutes)", fontweight='bold')
            ax.set_ylabel("Fat Oxidation (g/min)", fontweight='bold', color='tab:blue')
            ax.tick_params(axis='y', labelcolor='tab:blue')

            # CHO Oxidation on secondary axis
            ax2 = ax.twinx()
            ax2.scatter(df['Time'], df['CHOmin'], label='CHO Ox (g/min)', marker='o', color='tab:orange', s=10)
            ax2.set_ylabel("CHO Oxidation (g/min)", fontweight='bold', color='tab:orange')
            ax2.tick_params(axis='y', labelcolor='tab:orange')

            ax.set_title("Fat and CHO Oxidation over Time", fontweight='bold')
            ax.grid()

        # --- Plot: Ventilatory Equivalents + CO2 ---
        def plot_vent_co2(ax, df):
            """Plot ventilatory equivalents (VE/VO2, VE/VCO2) and PetCO2 over time."""
            ax.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue', s=10)
            ax.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green', s=10)

            ax.set_xlabel("Time (minutes)", fontweight='bold')
            ax.set_ylabel("VE/VO2 & VE/VCO2", fontweight='bold', color='tab:blue')
            ax.tick_params(axis='y', labelcolor='tab:blue')

            ax2 = ax.twinx()
            ax2.scatter(df['Time'], df['PetCO2'], label='PetCO2', marker='o', color='tab:orange', s=10)

            # Trendline for PetCO2
            z = np.polyfit(df['Time'], df['PetCO2'], 3)
            p = np.poly1d(z)
            x_trend = np.linspace(df['Time'].min(), df['Time'].max(), 100)
            ax2.plot(x_trend, p(x_trend), '--', color='orange', label='PetCO2 Trend')

            ax2.set_ylabel("PetCO2", fontweight='bold', color='tab:orange')
            ax2.tick_params(axis='y', labelcolor='tab:orange')

            ax.set_title("Ventilatory Equivalents & PetCO2 over Time", fontweight='bold')

            # --- Expand y-limits a little to make space for legend ---
            y1_min, y1_max = ax.get_ylim()
            ax.set_ylim(y1_min, y1_max + (y1_max - y1_min) * 0.15)

            y2_min, y2_max = ax2.get_ylim()
            ax2.set_ylim(y2_min, y2_max + (y2_max - y2_min) * 0.15)

            # Combine legends
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=8)
            ax.grid()

        # --- Plot: Ventilatory Equivalents + O2 ---
        def plot_vent_o2(ax, df):
            """Plot ventilatory equivalents (VE/VO2, VE/VCO2) and PetO2 over time."""
            ax.scatter(df['Time'], df['VE/VO2'], label='VE/VO2', marker='o', color='tab:blue', s=10)
            ax.scatter(df['Time'], df['VE/VCO2'], label='VE/VCO2', marker='o', color='tab:green', s=10)

            ax.set_xlabel("Time (minutes)", fontweight='bold')
            ax.set_ylabel("VE/VO2 & VE/VCO2", fontweight='bold', color='tab:blue')
            ax.tick_params(axis='y', labelcolor='tab:blue')

            ax2 = ax.twinx()
            ax2.scatter(df['Time'], df['PetO2'], label='PetO2', marker='o', color='tab:orange', s=10)

            # Trendline for PetO2
            z = np.polyfit(df['Time'], df['PetO2'], 3)
            p = np.poly1d(z)
            x_trend = np.linspace(df['Time'].min(), df['Time'].max(), 100)
            ax2.plot(x_trend, p(x_trend), '--', color='orange', label='PetO2 Trend')

            ax2.set_ylabel("PetO2", fontweight='bold', color='tab:orange')
            ax2.tick_params(axis='y', labelcolor='tab:orange')

            ax.set_title("Ventilatory Equivalents & PetO2 over Time", fontweight='bold')

            # --- Expand y-limits a little to make space for legend ---
            y1_min, y1_max = ax.get_ylim()
            ax.set_ylim(y1_min, y1_max + (y1_max - y1_min) * 0.15)

            y2_min, y2_max = ax2.get_ylim()
            ax2.set_ylim(y2_min, y2_max + (y2_max - y2_min) * 0.15)

            # Combine legends
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=8)
            ax.grid()

        # --- Plot: Respiratory Exchange Ratio (RER) ---
        def plot_rer(ax, df):
            """Plot Respiratory Exchange Ratio (RER) over time."""
            ax.scatter(df['Time'], df['RER'], label='RER', marker='o', s=10)

            ax.set_xlabel("Time (minutes)", fontweight='bold')
            ax.set_ylabel("RER", fontweight='bold')
            ax.set_title("Respiratory Exchange Ratio over Time", fontweight='bold')
            ax.legend(fontsize=8)
            ax.grid()

        # --- Return all plots together ---
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

    def generate_report_data(self):
        """Prepare client and test information to be displayed in the final PDF report."""

        # Fetch selected document from session
        document = st.session_state.get("selected_document")

        # Error handling if no document loaded
        if document is None:
            st.error("No client data found.")
            return None, None

        # Extract main sections
        client_info = document["VO2 Max Report Info"]["Client Info"]
        test_protocol = document["VO2 Max Report Info"]["Test Protocol"]
        results = test_protocol["Results"]

        # ==============================
        # Format client information
        # ==============================

        client_info_for_pdf = {
            "Name": client_info.get("Name"),
            "Sex": client_info.get("Sex"),
            "Age": client_info.get("Age"),
            "Height": client_info.get("Height"),
            "Weight": client_info.get("Weight")
        }

        # ==============================
        # Format test results information
        # ==============================

        # Guess the sport based on exercise device
        sport = "Unknown"
        if test_protocol.get("Exercise Device") == "Treadmill":
            sport = "Running"
        elif test_protocol.get("Exercise Device") == "Bike":
            sport = "Biking"

        test_results_for_pdf = {
            "Sport": sport,
            "Test Degree": test_protocol.get("Test Degree", "Unknown"),
            "Exercise Device": test_protocol.get("Exercise Device", "Unknown"),
            "Max VO2": results.get("Max VO2", "N/A"),
            "VO2max Percentile": results.get("VO2max Percentile", "N/A")
        }

        # ==============================
        # Store into Streamlit session for later use
        # (used during PDF generation)
        # ==============================
        st.session_state.client_data = client_info_for_pdf
        st.session_state.vo2_data = test_results_for_pdf

        # Return structured data
        return client_info_for_pdf, test_results_for_pdf

    def load_saved_report(self):
        """Load an existing saved report from MongoDB into Streamlit session state."""

        report_col = self.db["reports"]
        user_id = st.session_state.selected_client["_id"]
        test_id = st.session_state.selected_test["_id"]

        # Search MongoDB for an existing report for this client and test
        report = report_col.find_one({"user_id": user_id, "test_id": test_id})

        if report:
            # Restore Summary Text
            st.session_state.initial_report_text = report.get("summary", "")

            # ==============================
            # Restore Per-Plot Comments and Selection Flags
            # ==============================
            for plot in report.get("plots", []):
                idx = plot.get("index")
                title = plot.get("title")
                comment = plot.get("comment", "")
                include = plot.get("include", True)

                # Save each comment and inclusion flag separately into session
                st.session_state[f"comment_{idx}"] = comment
                st.session_state[f"include_{idx}"] = include

                # Initialize dictionary structures if missing
                if "plot_comments" not in st.session_state:
                    st.session_state.plot_comments = {}
                if "include_plot_flags" not in st.session_state:
                    st.session_state.include_plot_flags = {}

                # Save under titles for quick lookup later
                st.session_state.plot_comments[title] = comment
                st.session_state.include_plot_flags[title] = include

            # Return True if loading succeeded
            return True

        # No report found
        return False

    def report_builder(self):
        """Main function for building a VO2 Max report interactively inside Streamlit."""

        # Setup
        df = st.session_state.get("df")
        plot_functions = self.get_plot_functions()
        reports_col = self.db["reports"]

        # Initialize session state for plots if not already present
        if 'plot_comments' not in st.session_state:
            st.session_state.plot_comments = {}
        if 'include_plot_flags' not in st.session_state:
            st.session_state.include_plot_flags = {title: True for title, _ in plot_functions}

        st.subheader("📊 Plots & Comments")

        # ==============================
        # Plot Each Graph and Capture Comments
        # ==============================

        for i, (title, func) in enumerate(plot_functions):
            st.markdown(f"---")
            st.markdown(f"### {title}")

            # Plot the figure
            fig, ax = plt.subplots(figsize=(6, 3.5))
            func(ax, df)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=False)

            # Setup keys for session state
            include_key = f"include_{i}"
            comment_key = f"comment_{i}"
            plot_flag_dict = st.session_state.include_plot_flags
            comment_dict = st.session_state.plot_comments

            # Text box for comment
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("<div style='max-width: 400px;'>", unsafe_allow_html=True)
                comment = st.text_area(
                    "🗨️ Comments:",
                    key=comment_key,
                    height=100,
                    value=comment_dict.get(title, "")
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # Checkbox for including/excluding this plot
            with col2:
                include = st.checkbox("Include in Report", value=plot_flag_dict.get(title, True), key=include_key)

            # ==============================
            # Save Button for Each Section
            # ==============================
            if st.button(f"💾 Save '{title}' Section", key=f"save_{i}"):
                # Update session
                comment_dict[title] = comment
                plot_flag_dict[title] = include

                # Save the comment/inclusion immediately to MongoDB
                user_id = st.session_state.selected_client["_id"]
                test_id = st.session_state.selected_test["_id"]

                self.db["reports"].update_one(
                    {"user_id": user_id, "test_id": test_id},
                    {
                        "$set": {
                            f"plots.{i}": {
                                "index": i,
                                "title": title,
                                "comment": comment,
                                "include": include
                            },
                            "last_updated": datetime.utcnow()
                        },
                        "$setOnInsert": {
                            "summary": st.session_state.get("initial_report_text", "")
                        }
                    },
                    upsert=True
                )
                st.success(f"Saved section for '{title}' ✅")

        # ==============================
        # Summary Report Section
        # ==============================

        st.markdown("---")
        st.subheader("📝 Summary Report")

        # Initialize summary if missing
        if "initial_report_text" not in st.session_state:
            st.session_state.initial_report_text = ""

        st.session_state.initial_report_text = st.text_area(
            "Enter your summary or interpretation:",
            value=st.session_state.initial_report_text,
            height=150
        )

        # ==============================
        # Save All Sections Button
        # ==============================

        if st.button("💾 Save All Comments and Selections"):
            user_id = st.session_state.selected_client["_id"]
            test_id = st.session_state.selected_test["_id"]
            summary_text = st.session_state.initial_report_text

            plots_data = []
            for i, (title, _) in enumerate(plot_functions):
                comment = st.session_state.get(f"comment_{i}", "")
                include = st.session_state.get(f"include_{i}", True)

                st.session_state.plot_comments[title] = comment
                st.session_state.include_plot_flags[title] = include

                plots_data.append({
                    "index": i,
                    "title": title,
                    "comment": comment,
                    "include": include
                })

            # Also store the original test date in MongoDB
            report_info = st.session_state.selected_test.get("VO2 Max Report Info", {}).get("Report Info", {})
            test_date = report_info.get("Date", {})

            reports_col.update_one(
                {"user_id": user_id, "test_id": test_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "test_id": test_id,
                        "test_type": "VO2Max",
                        "summary": summary_text,
                        "plots": plots_data,
                        "last_updated": datetime.utcnow(),  # Date of report generation
                        "test_date": test_date               # Date of original test
                    }
                },
                upsert=True
            )
            st.success("✅ All comments and selections saved to MongoDB.")

        # Generate Final PDF Button
        if st.button("📄 Generate PDF Report"):
            self.generate_report_data()
            self.generate_pdf(self.s3_client)


    def generate_pdf(self, s3_client):
        """Generate the final PDF report from user inputs and upload it to S3."""

        # Setup
        df = st.session_state.get("df")
        plot_functions = self.get_plot_functions()
        client_data = st.session_state.get("client_data", {})
        vo2_data = st.session_state.get("vo2_data", {})
        plot_comments = st.session_state.get("plot_comments", {})
        initial_report_text = st.session_state.get("initial_report_text", "")

        # ==============================
        # Build PDF filename (Name + Test Date)
        # ==============================

        name = client_data.get("Name", "Unknown")

        # Extract test date for filename
        date_dict = st.session_state.selected_test.get("VO2 Max Report Info", {}).get("Report Info", {}).get("Date", {})
        if isinstance(date_dict, dict):
            year = str(date_dict.get("Year", ""))
            month = str(date_dict.get("Month", "")).zfill(2)
            day = str(date_dict.get("Day", "")).zfill(2)

            # Handle month names (convert to numbers)
            month_map = {
                "January": "01", "February": "02", "March": "03", "April": "04",
                "May": "05", "June": "06", "July": "07", "August": "08",
                "September": "09", "October": "10", "November": "11", "December": "12"
            }
            month = month_map.get(month, month)
            test_date_str = f"{year}-{month}-{day}"
        else:
            test_date_str = "unknown-date"

        # Final filename
        pdf_path = f"VO2MAX_report_{name.replace(',', '').replace(' ', '_')}_{test_date_str}.pdf"

        pdf_buffers = []

        # ==============================
        # Create Plot Images
        # ==============================

        include_flags = st.session_state.get("include_plot_flags", {})
        for plot_name, func in plot_functions:
            if not include_flags.get(plot_name, True):
                continue  # Skip plots that user chose not to include

            fig, ax = plt.subplots(figsize=(5.5, 3.5))
            func(ax, df)
            ax.set_title(plot_name, fontsize=15, fontweight='bold')
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="PNG")
            buf.seek(0)
            pdf_buffers.append((plot_name, buf, plot_comments.get(plot_name, "")))
            plt.close(fig)

        # ==============================
        # Setup PDF Document Template
        # ==============================

        from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, FrameBreak, PageBreak, NextPageTemplate

        doc = BaseDocTemplate(pdf_path, pagesize=LETTER)
        styles = getSampleStyleSheet()
        width, height = LETTER

        # Page layout settings
        doc.topMargin = 5
        doc.bottomMargin = 140
        doc.leftMargin = 72
        doc.rightMargin = 72
        header_height = 180
        body_height = height - doc.topMargin - doc.bottomMargin - header_height

        # Layout for the plot/comment pages
        plot_left_margin = 30
        plot_right_margin = 30
        usable_width = width - plot_left_margin - plot_right_margin
        half_width = (usable_width - 12) / 2  # 6pt gutter between plot frames

        # Define page templates
        doc.addPageTemplates([
            PageTemplate(
                id='ContentPage',
                frames=[
                    Frame(doc.leftMargin, doc.bottomMargin + body_height, doc.width, header_height, id='header'),
                    Frame(doc.leftMargin, doc.bottomMargin, doc.width / 2 - 6, body_height, id='left'),
                    Frame(doc.leftMargin + doc.width / 2 + 6, doc.bottomMargin, doc.width / 2 - 6, body_height, id='right'),
                    Frame(doc.leftMargin, doc.bottomMargin, doc.width, body_height, id='bottom')
                ]
            ),
            PageTemplate(
                id='PlotPage',
                frames=[
                    Frame(plot_left_margin, height - 350, half_width, 300, id='plot_left'),
                    Frame(plot_left_margin + half_width + 12, height - 350, half_width, 300, id='plot_right'),
                    Frame(plot_left_margin, doc.bottomMargin, usable_width, 350, id='comments')
                ]
            )
        ])

        # ==============================
        # Build Story (Content of PDF)
        # ==============================

        story = []

        # Add Logo
        logo_path = "graphics/CHAMPlogo.png"
        if logo_path and os.path.exists(logo_path):
            logo = Image(logo_path, width=100, height=100)
            logo.hAlign = "CENTER"
            story.append(logo)

        # Title + School
        story.extend([
            Paragraph("CHAMP Human Performance Lab Report", styles["Title"]),
            Paragraph('<para align="center">Southern Connecticut State University</para>', styles["Heading2"]),
            Spacer(1, 10),
            FrameBreak()
        ])

        # Athlete Info Table
        client_table_data = [["Client Info", ""]] + [[k, str(v)] for k, v in client_data.items()]
        client_table = Table(client_table_data, colWidths=[100, 120])
        client_table.setStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
        story.extend([client_table, FrameBreak()])

        # Test Results Table
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

        # Summary Report Section
        story.extend([
            Paragraph("<b>Summary Report:</b>", styles["Heading3"]),
            Spacer(1, 10),
            Paragraph(initial_report_text or "No report provided.", styles["Normal"]),
            Spacer(1, 20),
            NextPageTemplate('PlotPage'),
            PageBreak()
        ])

        # ==============================
        # Add Plots + Comments (2 plots per page)
        # ==============================

        for i in range(0, len(pdf_buffers), 2):
            left = pdf_buffers[i]
            right = pdf_buffers[i+1] if i+1 < len(pdf_buffers) else None

            # Add left and right plots
            for plot_buf in [left, right]:
                if not plot_buf:
                    continue
                plot_name, buf, _ = plot_buf
                img = Image(buf, width=half_width, height=190)
                img.hAlign = "CENTER"
                story.append(img)
                story.append(FrameBreak())

            # Add Comments
            story.append(Paragraph("<b>Comments:</b>", styles["Heading2"]))
            story.append(Spacer(1, 10))
            for plot_buf in [left, right]:
                if not plot_buf:
                    continue
                plot_name, _, comment = plot_buf
                story.append(Paragraph(f"<b>{plot_name}:</b>", styles["Normal"]))
                story.append(Paragraph(comment or "No comment provided.", styles["Normal"]))
                story.append(Spacer(1, 10))

            story.append(PageBreak())

        # ==============================
        # Build and Save PDF
        # ==============================

        doc.build(story)

        st.success("✅ PDF generated successfully!")
        #st.write("PDF saved as:", pdf_path)

        # Offer Download
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name=pdf_path)

        # Upload to AWS S3
        bucket_name = "champ-hpl-bucket"
        s3_key = f"reports/{os.path.basename(pdf_path)}"

        try:
            s3_client.upload_file(
                Filename=pdf_path,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs={
                    "ContentType": "application/pdf",
                    "ContentDisposition": "inline"
                }
            )
            st.success("📤 Report successfully uploaded to S3!")
        except Exception as e:
            st.error(f"❌ Upload failed: {e}")

        # Reset session state
        st.session_state.reviewing = False
