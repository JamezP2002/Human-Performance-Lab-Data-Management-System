import pandas as pd

class VO2MaxParser:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def parse(self) -> dict:
        df = self.df

        # Unstructured Data
        report_info = {
            "School": df.iloc[0, 0],
            "Date": {
                "Year": df.iloc[2, 1],
                "Month": df.iloc[2, 3],
                "Day": df.iloc[2, 5]
            },
            "Time": {
                "Hour": df.iloc[2, 6],
                "Minute": df.iloc[2, 8],
                "Second": df.iloc[2, 9]
            }
        }

        client_info = {
            "Name": df.iloc[5, 1],
            "Age": df.iloc[6, 1],
            "Height": round(df.iloc[7, 3]),
            "Sex": df.iloc[6, 4],
            "Weight": round(df.iloc[7, 6])
        }

        test_protocol = {
            "Test Degree": df.iloc[11, 1],
            "Exercise Device": df.iloc[12, 1],
            "Test Environment": {
                "Insp. Temp": df.iloc[14, 2],
                "Baro. Pressure": df.iloc[14, 5],
                "Insp. humid": df.iloc[14, 8],
                "Exp. flow temp.": df.iloc[15, 1],
                "Insp. O2": df.iloc[16, 1],
                "Insp. CO2": df.iloc[16, 4],
                "Selc. Flowmeter": df.iloc[17, 1],
                "STPD to BTPS": df.iloc[18, 1],
                "O2 Gain": df.iloc[18, 3],
                "CO2-NL gain": df.iloc[18, 5]
            },
            "Best Sampling Values": {
                "Base O2": df.iloc[21, 1],
                "Base CO2": df.iloc[21, 4],
                "Measured O2": df.iloc[21, 7],
                "Measured CO2": df.iloc[21, 10]
            }
        }

        # Structured Data
        start_row = 29
        end_row = start_row
        while end_row < len(df) and not (df.iloc[end_row, 0] == 'End' or pd.isna(df.iloc[end_row, 0])):
            end_row += 1

        # Extract tabular records
        if end_row <= start_row:
            tabular_records = []
        else:
            max_cols = 21 if df.shape[1] > 19 else 19
            cols = list(range(max_cols))
            table = df.iloc[start_row:end_row, cols]
            if max_cols > 19:
                table.columns = [
                    "Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE BTPS", "RER", "RR", "Vt BTPS",
                    "FEO2", "FECO2", "HR", "TM SPD", "TM GRD", "AcKcal", "PetCO2", "PetO2", "VE/VCO2", "VE/VO2", "FATmin", "CHOmin"
                ]
            else:
                table.columns = [
                    "Time", "VO2 STPD", "VO2/kg STPD", "Mets", "VCO2 STPD", "VE BTPS", "RER", "RR", "Vt BTPS",
                    "FEO2", "FECO2", "HR", "AcKcal", "PetCO2", "PetO2", "VE/VCO2", "VE/VO2", "FATmin", "CHOmin"
                ]
            tabular_records = table.to_dict(orient="records")

        # Results extraction
        results_row = end_row + 2
        max_vo2 = None
        if results_row < len(df):
            raw_max = df.iloc[results_row, 3]
            if pd.notna(raw_max):
                max_vo2 = round(float(raw_max), 2)

        vo2_percentile = None
        if results_row + 2 < len(df):
            raw_pct = df.iloc[results_row + 2, 1]
            if isinstance(raw_pct, str):
                vo2_percentile = raw_pct.split()[0]
            elif pd.notna(raw_pct):
                vo2_percentile = raw_pct

        results = {}
        if max_vo2 is not None:
            results["Max VO2"] = max_vo2
        if vo2_percentile is not None:
            results["VO2max Percentile"] = vo2_percentile

        test_protocol["Results"] = results

        # Final payload
        parsed = {
            "Report Info": report_info,
            "Client Info": client_info,
            "Test Protocol": test_protocol,
            "Tabular Data": tabular_records
        }
        return parsed