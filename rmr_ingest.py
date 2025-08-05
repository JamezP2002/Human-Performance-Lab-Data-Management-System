import pandas as pd
import streamlit as st

class RMRParser:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def parse(self) -> dict:
        df = self.df

        # Unstructured Data
        report_info = {
            "School": df.iloc[0,0],
            "Date": {
                "Year": df.iloc[2, 1],
                "Month":df.iloc[2, 3],
                "Day": df.iloc[2, 5]
            },
            "Time": {
                "Hour": df.iloc[2, 6], 
                "Minute": df.iloc[2, 8], 
                "Second": df.iloc[2, 9]
            }}

        client_info = {
            "Name": df.iloc[5, 1],
            "Age": df.iloc[6, 1],
            "Height": df.iloc[7, 1],
            "Sex": df.iloc[6, 4],
            "Weight": df.iloc[7, 6],   
        }

        test_protocol = {
            "Test Degree": df.iloc[11,1],
            "Exercise Device": df.iloc[12,1],
            "Test Enviroment": {"Insp. Temp": df.iloc[14,2], 
                                "Baro. Pressure": df.iloc[14,5],
                                "Insp. humid": df.iloc[14,8],
                                "Exp. flow temp.": df.iloc[15, 3],
                                "Insp. O2": df.iloc[16, 1],
                                "Insp. CO2": df.iloc[16,4],
                                "Selc. Flowmeter": df.iloc[17, 1],
                                "STPD to BTPS": df.iloc[18, 1],
                                "O2 Gain": df.iloc[18, 3],
                                "CO2-NL gain": df.iloc[18, 5]},
            "Best Sampling Values": {"Base O2": df.iloc[21, 1],
                                    "Base CO2": df.iloc[21, 4],
                                    "Measured O2": df.iloc[21, 7],
                                    "Measured CO2": df.iloc[21, 10]},
            "Results": {"Avg RMR": 0.0,
                        "Predicted RMR": 0.0,
                        "RQ": 0.0}  # Placeholders
        }

        # Structured Data
        #if df.iloc[29:118, 0:11].empty:
        #    st.write("No tabular data")
        #else:
        #    tabular_data_raw = df.iloc[29:118, 0:11]
        #    tabular_data_raw.columns = ["Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE uncor.", "RQ", "FEO2", "FECO2", "REE", "RMR"]

        #tabular_data = tabular_data_raw.to_dict(orient="records")

        # Structured Data
        start_row = 29
        end_row = start_row
        while end_row < len(df) and not (df.iloc[end_row, 0] == 'End' or pd.isna(df.iloc[end_row, 0])):
            end_row += 1

        # Extract tabular records
        if end_row <= start_row:
            tabular_data = []
        else:
            max_cols = 11
            cols = list(range(max_cols))
            table = df.iloc[start_row:end_row, cols]
            table.columns = ["Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE uncor.", "RQ", "FEO2", "FECO2", "REE", "RMR"]

            tabular_data = table.to_dict(orient="records")

        # Calculate average RMR from 10 minutes to the end of the test
        records_after_10 = [row for row in tabular_data if row["Time"] >= 10]

        if records_after_10:
            # sum up the RMR column, then divide by how many rows we have
            total_rmr = sum(row["RMR"] for row in records_after_10)
            total_vco2 = sum(row["VCO2 STPD"] for row in records_after_10)
            total_vo2 = sum(row["VO2 STPD"] for row in records_after_10)
            avg_rmr = total_rmr / len(records_after_10)
        else:
            avg_rmr = 0.0 

        test_protocol["Results"]["Avg RMR"] = round(avg_rmr) if avg_rmr is not None else None

        # Calculate the Mifflin-St Jeor equation for RMR
        sex = client_info["Sex"]
        weight_lb = client_info["Weight"]
        height_in = client_info["Height"]
        # convert weight to kg and height to cm
        weight_kg = weight_lb * 0.453592
        height_cm = height_in * 2.54
        age_years = client_info["Age"]

        if sex.lower() == 'm':
            predicted_rmr = 66 + (13.7 * weight_kg) + (5 * height_cm) - (6 * age_years) 
        elif sex.lower() == 'f':
            predicted_rmr = 655 + (9.6 * weight_kg) + (1.7 * height_cm) - (4.7 * age_years) 
        else:
            raise ValueError("Gender must be 'male' or 'female'.")
        
        test_protocol["Results"]["Predicted RMR"] = round(predicted_rmr) if predicted_rmr is not None else None

        # Calculate the RQ 
        rq = total_vco2 / total_vo2 if total_vo2 > 0 else 0.0
        test_protocol["Results"]["RQ"] = round(rq, 2) if rq is not None else None

        parsed = {
            "Report Info": report_info,
            "Client Info": client_info,
            "Test Protocol": test_protocol,
            "Tabular Data": tabular_data
        }
        return parsed