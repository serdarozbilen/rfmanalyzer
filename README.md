# RFM Analyzer

RFM Analyzer is a web-based tool that helps businesses analyze their customer base using the RFM (Recency, Frequency, Monetary) methodology. Upload your customer transaction data and get detailed RFM analysis and customer segmentation.

## Features

- CSV file upload for customer transaction data
- Automated RFM analysis
- Customer segmentation
- Downloadable results in CSV format
- Visual representations of customer segments

## Required CSV Format

Your input CSV file should have the following columns:
- customer_id: Unique identifier for each customer
- transaction_date: Date of the transaction (YYYY-MM-DD format)
- transaction_amount: Amount of the transaction

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app/main.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Prepare your customer transaction data in CSV format
2. Upload the CSV file through the web interface
3. View the RFM analysis results
4. Download the segmented customer list 