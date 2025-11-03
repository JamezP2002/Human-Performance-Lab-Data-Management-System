# Human Performance Lab Data Management System

## Overview
This project is a **Human Performance Lab Data Management System** designed to streamline the storage, processing, and visualization of physiological test data at the CHAMP Human Performance Lab, specifically right now the  **VO2 Max** and **Resting Metabolic Rate (RMR) tests**. The system utilizes **MongoDB** for data storage, **Pandas** for data handling, and **Streamlit** for an interactive web-based interface.

## Features
### Implemented Tests:
- **VO2 Max Test**: Implemented. Key features added:
  - Parses VO2 Max test documents (Excel/JSON) and converts tabular data into a pandas DataFrame for analysis and display.
  - Interactive Streamlit workflow to:
    - Render all diagnostic plots and collect per‑plot comments.
    - Toggle inclusion/exclusion of individual plots.
    - Save per‑plot comments and report summary to MongoDB.
  - Plotting utilities include:
    - V‑Slope analysis with ventilatory threshold detection.
    - VO2 uptake over time with trendline.
    - Heart rate over time.
    - Fat and carbohydrate (CHO) oxidation rates with dual y‑axis.
    - Ventilatory equivalents with end‑tidal CO2 and O2 tensions.
    - Respiratory exchange ratio (RER) over time.
  - PDF report generation using ReportLab:
    - Custom layout with logo, title, client info and test results side‑by‑side, charts (2 per page) and comments.
    - Output saved locally, downloadable via Streamlit, and optionally uploaded to AWS S3.
  - Session state integration for seamless review/edit/save cycles inside Streamlit.
  - Reports stored/updated in MongoDB with plot metadata (index, title, comment, include flag) and test date.

- **Resting Metabolic Rate (RMR) Test**: Implemented. Key features added:
  - Parses RMR test documents and converts tabular data into a pandas DataFrame for analysis and display.
  - Interactive Streamlit workflow to:
    - Display plots and collect per‑plot comments.
    - Toggle inclusion/exclusion of individual plots.
    - Save per‑plot comments and report summary to MongoDB.
  - Plotting utilities include:
    - RMR over time with optional trend line.
    - Total Daily Energy Expenditure (TDEE) pie chart.
  - PDF report generation using ReportLab:
    - Custom layout with logo, title, client info and test results side‑by‑side, charts, summary, and comments.
    - Output saved locally and offered for download in Streamlit.
    - Optional upload to AWS S3 (configurable via environment variables).
  - Session state integration for seamless review/edit/save cycles.
  - Reports stored/updated in MongoDB with plot metadata (index, title, comment, include flag) and test date.

### Data Processing:
- Parses **Excel files** containing test results
- Extracts and structures **patient info, test protocols, and tabular data**
- Stores data into **MongoDB** for retrieval and analysis

### Interactive Dashboard:
- Allows users to **upload Excel files**
- Displays **structured and unstructured data**
- Provides **multiple visualizations** for key metrics

## Technology Stack
- **Python**
- **Pandas** (Data Processing)
- **MongoDB** (Database)
- **Streamlit** (Web Interface & Visualization)
- **Matplotlib** (Data Visualization)
- **dotenv** (Environment Variables Management)
- **Aws** (hosting the application online)

## Installation & Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/JamezP2002/human-peformance-lab-capstone.git
   cd performance-lab
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file in the root directory.
   - Add your MongoDB connection string:
     ```plaintext
     database_credentials = your_mongodb_connection_string
     ```

5. **Run the Streamlit app:**
   ```bash
   streamlit run streamlit_app.py
   ```

## Usage (as of 2/15/2025)
- Upload an **Excel file** containing test data.
- View **parsed patient and test information**.
- Analyze **visualizations** to interpret results.

## Future Improvements
- Implement additional tests beyond **VO2 Max** and **RMR**.
- Enhance **data validation and error handling**.
- Implement **exporting features** for report generation.
- Implement **Reports** to generate a report for the user. 

## License
This project is licensed for the CHAMP lab at SCSU.

## Contact
For any questions or collaboration, feel free to reach out!

---
*This project is part of my capstone initiative focused on modernizing data management for the CHAMP Human Performance Lab.*

