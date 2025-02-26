# Human Performance Lab Data Management System

## Overview
This project is a **Human Performance Lab Data Management System** designed to streamline the storage, processing, and visualization of physiological test data at the CHAMP Human Performance Lab, specifically right now the  **VO2 Max** and **Resting Metabolic Rate (RMR) tests**. The system utilizes **MongoDB** for data storage, **Pandas** for data handling, and **Streamlit** for an interactive web-based interface.

## Features
### Implemented Tests:
- **VO2 Max Test**: Extracts relevant data from an uploaded Excel file, structures it into JSON format, and stores it in MongoDB. Generates visualizations such as:
  - V-Slope 
  - VO2 over time
  - Heart rate over time
  - Fat and carbohydrate oxidation rates
  - Ventilatory equivalents & end-tidal CO2/O2 tension
  - Respiratory exchange ratio (RER)
- **Resting Metabolic Rate (RMR) Test**: (Implementation details TBD)

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

## Usage
- Upload an **Excel file** containing test data.
- View **parsed patient and test information**.
- Analyze **visualizations** to interpret results.
- TBD: Create **Reports** for the end user to review their results.

## Future Improvements
- Implement additional tests beyond **VO2 Max** and **RMR**.
- Enhance **data validation and error handling**.
- Add **user authentication** for secure access.
- Implement **exporting features** for report generation.
- Implement **Reports** to generate a report for the user. 

## License
This project is licensed for the CHAMP lab at SCSU.

## Contact
For any questions or collaboration, feel free to reach out!

---
*This project is part of my capstone initiative focused on modernizing data management for the CHAMP Human Performance Lab.*

