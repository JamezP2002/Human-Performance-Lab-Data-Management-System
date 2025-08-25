import pandas as pd
from pymongo import MongoClient
import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv, find_dotenv
import boto3
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, KeepTogether, KeepInFrame, Paragraph, Spacer
import io
import numpy as np
from datetime import datetime
import time

class RMRTest:
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
        """Parse the provided document and load it into Streamlit session."""
        try:
            # Save entire document to session
            st.session_state.selected_document = document

            # Break apart key data sections
            report_info = document["RMR Report Info"]
            client_info = report_info["Client Info"]
            test_protocol = report_info["Test Protocol"]
            results = test_protocol["Results"]
            tabular_data = report_info["Tabular Data"]

            self.results = results

            # Convert tabular data into dataframe for easy use
            df = pd.DataFrame(tabular_data)

            # Store DataFrame in session
            st.session_state.df = df

            return client_info, test_protocol, results, df

        except Exception as e:
            st.error(f"Failed to parse test document: {e}")
            return None

    def get_plot_functions(self):
        """Return list of plotting functions for different test metrics."""
        df = st.session_state.get("df")

        # Time-Series Plot of RMR (kcal/day)
        def plot_rmr_over_time(ax, df):
            """Plot RMR over time."""
            ax.plot(df["Time"], df["REE"], label="RMR (kcal/day)", color='blue')
            ax.set_xlabel("Time (minutes)")
            ax.set_ylabel("RMR (kcal/day)")
            ax.set_title("RMR Over Time", fontsize=7, fontweight='bold')
            ax.grid(True)
            ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1), fontsize='small')

            # Add trend line after 10 minutes to show RMR stability
            if len(df) > 10:
                x = df["Time"][10:]
                y = df["REE"][10:]
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                ax.plot(x, p(x), color='red', linestyle='--', label="Trend Line")
                ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1), fontsize='small')

        # Bullet Gauge for Respiratory Quotient (RQ)
        def draw_rq_bullet(ax, df):

            rq_value = self.results.get("RQ", 0.0)

            colors_rq = [
                "#FF4C4C",  # red (Check)
                "#FFA500",  # orange (High)
                "#4CAF50",  # green (Normal)
                "#1E90FF"   # blue (Low)
            ]

            """
            Draw a bullet gauge for Respiratory Quotient (RQ).
            Zones (default matplotlib colors):
            • <0.63  (“Check”)
            • 0.63–0.78  (“High”)
            • 0.78–0.93  (“Normal”)
            • 0.93–1.00  (“Low”)
            • >1.00  (“Check”)
            """
            # Define breakpoints
            min_val, zone1, zone2, zone3, max_val = 0.50, 0.63, 0.78, 0.93, 1.00

            # Draw each zone as a horizontal bar
            ax.barh(0, zone1 - min_val, left=min_val, height=0.4, color=colors_rq[0], label="Check")
            ax.barh(0, zone2 - zone1, left=zone1, height=0.4, color=colors_rq[1], label="High")
            ax.barh(0, zone3 - zone2, left=zone2, height=0.4,  color=colors_rq[2], label="Normal")
            ax.barh(0, max_val - zone3, left=zone3, height=0.4, color=colors_rq[3], label="Low")

            # Draw the “pointer”
            ax.plot([rq_value], [0], marker='v', markersize=12)

            # Clean up axes
            ax.set_xlim(min_val, max_val)
            ax.set_yticks([])
            ax.set_xlabel("Respiratory Quotient (RQ)")
            ax.set_title("Metabolic Efficiency (RQ)")
            ax.tick_params(axis='x', which='both', length=0)
            ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1), fontsize='small')
    
        # Bullet Gauge for Resting Energy Expenditure (REE)
        def plot_ree_bullet(ax, df):
            """
            Draw a bullet gauge for Resting Energy Expenditure (REE).
            Expects in `self.results["REE"]` your measured kcal/day,
            and `self.results["LLN"]`, `self.results["ULN"]` the normative bounds.
            """

            # pull values out of the parsed results
            ree = getattr(self, "results", {}).get("Avg RMR", 0)

            lln = 1000
            uln = 2082

            # define the chart span
            min_val = 0
            max_val = uln * 1.3  # give some padding beyond ULN

            # Custom colors
            slow_color = "#FF4C4C"   # red
            normal_color = "#4CAF50" # green
            fast_color = "#1E90FF"   # blue

            # draw the slow, normal, fast zones
            ax.barh(0, lln - min_val,   left=min_val, height=0.4, label="Slow", color=slow_color)
            ax.barh(0, uln - lln,       left=lln,    height=0.4, label="Normal", color=normal_color)
            ax.barh(0, max_val - uln,   left=uln,    height=0.4, label="Fast", color=fast_color)

            # draw the pointer
            ax.plot([ree], [0], marker="v", markersize=12, color="black")

            # formatting
            ax.set_xlim(min_val, max_val)
            ax.set_yticks([])
            ax.set_xlabel("REE (kcal/day)")
            ax.set_title("Resting Energy Expenditure (REE)")
            ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1), fontsize='small')

        # TDEE pie chart (USER INPUT REQUIRED)
        def plot_tdee_pie(ax, df, activity_level = None):
            # Pull BMR (or RMR) from your calculated results
            bmr = getattr(self, "results", {}).get("Avg RMR", 0)
            #print(f"Using BMR: {bmr}")

            if activity_level is None:
                activity_level = st.session_state.get("activity_level")

            # Simple presets for EAT/NEAT (kcal/day).
            presets = {
                "sedentary":   {"eat": 100, "neat": 200},
                "light":       {"eat": 200, "neat": 300},
                "moderate":    {"eat": 300, "neat": 400},
                "active":      {"eat": 450, "neat": 550},
                "very active": {"eat": 600, "neat": 700},
            }
            eat = presets[activity_level]["eat"]
            neat = presets[activity_level]["neat"]

            # TEF as exact 10% of TDEE
            tef_pct = 0.10
            base = bmr + eat + neat
            tdee_total = base / (1 - tef_pct) if base > 0 else 0.0
            tef = tef_pct * tdee_total

            labels = ["BMR", "TEF", "EAT", "NEAT"]
            sizes  = [bmr, tef, eat, neat]
            colors = ["#0080ff", '#ff9999', '#99ff99', '#ffcc99']

            def fmt(pct):
                kcal = pct * tdee_total / 100.0
                return f"{pct:.1f}%\n({kcal:.0f} kcal)"

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct=fmt,
                startangle=90,
                colors=colors,
                textprops={'fontsize': 8}
            )
            ax.axis('equal')
            ax.set_title("Total Daily Energy Expenditure (Actual)", fontsize=16, fontweight="bold")

        # TDEE pie chart (NORMALIZED)
        def plot_predicted_tdee_pie(ax, df, activity_level = None):
            # Pull BMR (or RMR) from your calculated results
            bmr = getattr(self, "results", {}).get("Predicted RMR", 0)
            #print(f"Using BMR: {bmr}")

            if activity_level is None:
                activity_level = st.session_state.get("activity_level")

            # Simple presets for EAT/NEAT (kcal/day).
            presets = {
                "sedentary":   {"eat": 100, "neat": 200},
                "light":       {"eat": 200, "neat": 300},
                "moderate":    {"eat": 300, "neat": 400},
                "active":      {"eat": 450, "neat": 550},
                "very active": {"eat": 600, "neat": 700},
            }
            eat = presets[activity_level]["eat"]
            neat = presets[activity_level]["neat"]

            # TEF as exact 10% of TDEE
            tef_pct = 0.10
            base = bmr + eat + neat
            tdee_total = base / (1 - tef_pct) if base > 0 else 0.0
            tef = tef_pct * tdee_total

            labels = ["BMR", "TEF", "EAT", "NEAT"]
            sizes  = [bmr, tef, eat, neat]
            colors = ["#0080ff", "#ff9100", "#fbff00", "#777777"]

            def fmt(pct):
                kcal = pct * tdee_total / 100.0
                return f"{pct:.1f}%\n({kcal:.0f} kcal)"

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct=fmt,
                startangle=90,
                colors=colors,
                textprops={'fontsize': 8}
            )
            ax.axis('equal')
            ax.set_title("Total Daily Energy Expenditure (Predicted)", fontsize=16, fontweight="bold")


        plot_functions = [
            ("RMR Over Time", plot_rmr_over_time),
            ("TDEE Breakdown", plot_tdee_pie),
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
        client_info = document["RMR Report Info"]["Client Info"]
        test_protocol = document["RMR Report Info"]["Test Protocol"]
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

        test_results_for_pdf = {
            "Avg RMR": results.get("Avg RMR", 0.0),
            "Predicted RMR": results.get("Predicted RMR", 0.0),
            "RQ": results.get("RQ", 0.0),
        }

        # ==============================
        # Store into Streamlit session for later use
        # (used during PDF generation)
        # ==============================
        st.session_state.client_data = client_info_for_pdf
        st.session_state.rmr_data = test_results_for_pdf

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
        """Main function for building a report interactively inside Streamlit."""

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
            height = 4
            fig, ax = plt.subplots(figsize = (6,height))
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
                with st.expander("Add Comments", expanded=False):
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
                include = st.toggle("Include in Report", value=plot_flag_dict.get(title, True), key=include_key)

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
            progress_bar = st.progress(0, "Saving all comments and selections...")
            for pct in range(101):
                time.sleep(0.005)  # brief pause to show animation
                progress_bar.progress(pct, "Saving all comments and selections...")

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
            report_info = st.session_state.selected_test.get("RMR Report Info", {}).get("Report Info", {})
            test_date = report_info.get("Date", {})

            reports_col.update_one(
                {"user_id": user_id, "test_id": test_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "test_id": test_id,
                        "test_type": "RMR",
                        "summary": summary_text,
                        "plots": plots_data,
                        "last_updated": datetime.utcnow(),  # Date of report generation
                        "test_date": test_date # Date of original test
                    }
                },
                upsert=True
            )
            st.success("All comments and selections saved to MongoDB.")
            st.balloons()

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
        report_data = st.session_state.get("data", {})
        plot_comments = st.session_state.get("plot_comments", {})
        initial_report_text = st.session_state.get("initial_report_text", "")

        # ==============================
        # Build PDF filename (Name + Test Date)
        # ==============================

        name = client_data.get("Name", "Unknown")

        # Extract test date for filename
        date_dict = st.session_state.selected_test.get("RMR Report Info", {}).get("Report Info", {}).get("Date", {})
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
        pdf_path = f"RMR_report_{name.replace(',', '').replace(' ', '_')}_{test_date_str}.pdf"

        pdf_buffers = []

        # ==============================
        # Create Plot Images
        # ==============================

        include_flags = st.session_state.get("include_plot_flags", {})
        for plot_name, func in plot_functions:
            if not include_flags.get(plot_name, True):
                continue  # Skip plots that user chose not to include

            height = 3 if "RMR" in plot_name else 4
            width = 5.5 if "RMR" in plot_name else 6
            fig, ax = plt.subplots(figsize=(width, height))
            func(ax, df)
            ax.set_title(plot_name, fontsize=12 if "RMR" in plot_name or "TDEE" in plot_name else 8 , fontweight='bold')
            if "TDEE" in plot_name:
                texts = ax.texts
                for text in texts:
                    text.set_fontsize(10)
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="PNG")
            buf.seek(0)
            pdf_buffers.append((plot_name, buf, plot_comments.get(plot_name, "")))
            plt.close(fig)

        DEBUG = False

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(LETTER),  
            leftMargin=20,
            rightMargin=20,
            topMargin=0,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()
        story = []

        # === Add Logo ===

        story.append(Spacer(1, -20))
        logo_path = "graphics/CHAMPlogo.png"
        if logo_path and os.path.exists(logo_path):
            logo = Image(logo_path, width=100, height=100)
            # put logo inside a 1x1 table so we can draw a border around it
            logo_table = Table([[logo]], colWidths=[100], rowHeights=[100])
            logo_table.setStyle([
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("ALIGN",  (0,0), (-1,-1), "CENTER"),
                *([("BOX", (0,0), (-1,-1), 1, colors.blue)] if DEBUG else []),
            ])
            story.append(logo_table)
        else:
            st.warning("Logo file not found, skipping logo in PDF.")

        story.append(Spacer(1, -20))

        # === Title + School ===
        title_para = Paragraph("CHAMP Human Performance RMR Report", styles["Title"])
        subtitle_para = Paragraph('<para align="center">Southern Connecticut State University</para>', styles["Heading2"])

        title_block = Table([[title_para], [subtitle_para]], colWidths=[doc.width])
        title_block.setStyle([
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN",(0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            *([("BOX", (0,0), (-1,-1), 1, colors.green)] if DEBUG else []),
        ])
        story.append(title_block)
        story.append(Spacer(1, 5))

        # Two Tables for Client Info and Test Results
        client_info = st.session_state.get("client_data", {})
        test_results = st.session_state.get("rmr_data", {})
        if not client_info or not test_results:
            st.error("Client data or test results are missing.")
            return
        
        # === Client Info Table ===
        client_info_data = [
            ["Client Information", ""],
            ["Name", client_info.get("Name", "N/A")],
            ["Age", client_info.get("Age", "N/A")],
            ["Sex", client_info.get("Sex", "N/A")],
            ["Height", client_info.get("Height", "N/A")],
            ["Weight", client_info.get("Weight", "N/A")]
        ]

        client_info_table = Table(client_info_data, colWidths=[100, 140])
        client_info_table.setStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6F2FF")),  
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0077CC")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),   
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ])
        client_info_table.hAlign = "LEFT"

        #story.append(client_info_table)
        #story.append(Spacer(1, 5))

        # === Test Results Table ===
        test_results_data = [
            ["Test Results", ""],
            ["Avg RMR (kcal/day)", test_results.get("Avg RMR", "N/A")],
            ["Predicted RMR (kcal/day)", test_results.get("Predicted RMR", "N/A")],
            ["RQ", test_results.get("RQ", "N/A")]
        ]
        
        test_results_table = Table(test_results_data, colWidths=[140, 100])

        # --- base style ---
        style = [
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6F2FF")),  
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0077CC")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),   
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]

        # --- styling for texts ---
        style += [
            ("TEXTCOLOR", (1,1), (1,1), colors.red),   # Avg RMR value
            ("FONTNAME",  (0,1), (1,1), "Helvetica-Bold"),  # Avg RMR row bold

            ("TEXTCOLOR", (1,3), (1,3), colors.red),  # RQ value
            ("FONTNAME",  (0,3), (1,3), "Helvetica-Bold"),  # RQ row bold
        ]

        test_results_table.setStyle(TableStyle(style))

        # --- helper to convert a buffer to an Image flowable ---
        def _img(buf, w, h):
            im = Image(buf, width=w, height=h)
            im.hAlign = "CENTER"
            return im

        # --- pull RMR chart safely ---
        chart_buf = pdf_buffers[0] if len(pdf_buffers) > 0 else None
        chart_data = chart_buf[1] if (chart_buf and isinstance(chart_buf, (list, tuple)) and len(chart_buf) > 1) else None

        # --- sizes ---
        usable  = doc.width
        left_w  = 300                      # fixed left column (tables)
        right_w = usable - left_w          # remaining width for the chart
        chart_h = 200

        # --- left: stack tables vertically ---
        left_stack = Table(
            [[client_info_table],
             ["========================================="],
            [test_results_table]],
            colWidths=[left_w]
        )
        left_stack.setStyle([
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0), (-1,-1), 0),
        ] + ([("BOX",(0,0),(-1,-1),0.75,colors.red)] if DEBUG else []))

        # --- right: single image or spacer ---
        right_cell = _img(chart_data, right_w, chart_h) if chart_data else Spacer(1, chart_h)

        right_column = Table([[right_cell]], colWidths=[right_w])
        right_column.setStyle([
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0), (-1,-1), 0),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN",(0,0), (-1,-1), "MIDDLE"),
        ] + ([("BOX",(0,0),(-1,-1),0.75,colors.green)] if DEBUG else []))

        # --- outer table: [ left_stack | right_column ] ---
        main_top = Table([[left_stack, right_column]], colWidths=[left_w, right_w])
        main_top.hAlign = "CENTER"
        main_top.setStyle([
            ("VALIGN",      (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING",(0,0), (-1,-1), 0),
            ("TOPPADDING",  (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ])

        story.append(main_top)
        story.append(Spacer(1, 12))

        # --- layout ---
        gutter = 8
        pie_h  = 220
        pie_w  = (doc.width - gutter) * 0.50          # ~34% left for pie
        sum_w  = doc.width - pie_w - gutter           # remainder for summary

        # --- pie image or spacer ---
        reg_pie_buf = pdf_buffers[1][1] 
        img_cell = _img(reg_pie_buf, pie_w, pie_h) if reg_pie_buf else Spacer(1, pie_h)
        if hasattr(img_cell, "hAlign"):
            img_cell.hAlign = "LEFT"

        # --- summary block ---
        summary_text = st.session_state.get("initial_report_text") or "No report provided."
        summary_block = KeepInFrame(
            sum_w, pie_h,
            [
                Paragraph("<b>Summary Report</b>", styles["Heading3"]),
                Spacer(1, 6),
                Paragraph(summary_text, styles["Normal"]),
            ],
            mode="shrink"
        )

        # --- 1 row, 2 columns: [pie | summary] ---
        pie_table = Table(
            [[img_cell, summary_block]],
            colWidths=[pie_w, sum_w],
            rowHeights=[pie_h]
        )
        pie_table.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("ALIGN",        (0, 0), (0, 0),   "LEFT"),   # left column left-aligned
            ("LEFTPADDING",  (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
            # ("GRID", (0,0), (-1,-1), 0.25, colors.grey),  # debug
        ]))

        story.append(KeepTogether([pie_table, Spacer(1, 6)]))

        # if there is comments for any plots or charts, add them underneath
        for plot_name, buf, comment in pdf_buffers:
            if not comment.strip():
                continue
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>{plot_name} Comments:</b>", styles["Heading3"]))
            story.append(Paragraph(comment, styles["Normal"]))
            story.append(Spacer(1, 6))

        # === Footer with Solid Blue Line ===
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(colors.HexColor("#0077CC"))  # solid blue
            canvas.rect(
                x=doc.leftMargin,
                y=15,  # 15 points from bottom
                width=doc.width,
                height=10,
                fill=True,
                stroke=0
            )
            canvas.restoreState()

        # Build PDF 
        doc.build(story, onFirstPage=footer, onLaterPages=footer)

        st.success("✅ PDF generated successfully!")
        #st.write("PDF saved as:", pdf_path)

        # Offer Download
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name=pdf_path)

        # Upload to AWS S3
        # bucket_name = "champ-hpl-bucket"
        # s3_key = f"reports/{os.path.basename(pdf_path)}"

        # try:
        #     s3_client.upload_file(
        #         Filename=pdf_path,
        #         Bucket=bucket_name,
        #         Key=s3_key,
        #         ExtraArgs={
        #             "ContentType": "application/pdf",
        #             "ContentDisposition": "inline"
        #         }
        #     )
        #     st.success("📤 Report successfully uploaded to S3!")
        # except Exception as e:
        #     st.error(f"❌ Upload failed: {e}")

        # Reset session state
        st.session_state.reviewing = False
