import pandas as pd
import numpy as np
from datetime import datetime

class RFMAnalyzer:
    def __init__(self, df):
        """
        Initialize RFM Analyzer with a pandas DataFrame
        
        Parameters:
        df (pandas.DataFrame): DataFrame containing customer transaction data
        """
        self.df = df
        self.rfm = None
        self.segment_labels = {
            'Champions': 'Most Valuable Customers',
            'Loyal': 'Loyal Customers',
            'Recent': 'Recent Customers',
            'Promising': 'Promising Customers',
            'Attention': 'Customers Needing Attention',
            'Lost': 'Lost Customers'
        }

    def preprocess_data(self):
        """Preprocess the data for RFM analysis"""
        # Convert transaction_date to datetime if it's not already
        self.df['transaction_date'] = pd.to_datetime(self.df['transaction_date'])
        
        # Remove any negative transaction amounts
        self.df = self.df[self.df['transaction_amount'] > 0]

    def calculate_metric_scores(self, values, labels, ascending=True):
        """
        Calculate scores for a metric, handling small datasets and duplicate values
        
        Parameters:
        values (Series): The values to score
        labels (range): The labels to use for scoring
        ascending (bool): Whether to sort values in ascending order
        """
        unique_values = len(values.unique())
        
        if unique_values < 4:
            # If we have less than 4 unique values, use rank-based scoring
            ranks = values.rank(method='dense', ascending=ascending)
            max_rank = ranks.max()
            scores = ((ranks - 1) * (3) / (max_rank - 1) + 1).astype(int)
            return scores
        else:
            try:
                # Try regular quartile-based scoring first
                return pd.qcut(values, q=4, labels=labels, duplicates='drop')
            except ValueError:
                # If that fails, fall back to rank-based scoring
                ranks = values.rank(method='dense', ascending=ascending)
                max_rank = ranks.max()
                scores = ((ranks - 1) * (3) / (max_rank - 1) + 1).astype(int)
                return scores

    def calculate_rfm_scores(self, analysis_date=None):
        """
        Calculate RFM scores for each customer
        
        Parameters:
        analysis_date (datetime, optional): The date to use as reference for recency calculation
        """
        if analysis_date is None:
            analysis_date = self.df['transaction_date'].max()
        else:
            analysis_date = pd.to_datetime(analysis_date)

        # Group by customer and calculate RFM metrics
        rfm_data = self.df.groupby('customer_id').agg({
            'transaction_date': lambda x: (analysis_date - x.max()).days,  # Recency
            'transaction_amount': ['count', 'sum']  # Frequency and Monetary
        })

        # Flatten column names
        rfm_data.columns = ['recency', 'frequency', 'monetary']

        # Calculate scores for each metric
        r_labels = range(4, 0, -1)  # 4 is best for recency (lowest number of days)
        f_labels = range(1, 5)      # 4 is best for frequency (highest number of transactions)
        m_labels = range(1, 5)      # 4 is best for monetary (highest amount spent)

        rfm_data['R'] = self.calculate_metric_scores(rfm_data['recency'], r_labels, ascending=True)
        rfm_data['F'] = self.calculate_metric_scores(rfm_data['frequency'], f_labels, ascending=False)
        rfm_data['M'] = self.calculate_metric_scores(rfm_data['monetary'], m_labels, ascending=False)
        
        # Calculate RFM Score
        rfm_data['RFM_Score'] = rfm_data['R'].astype(str) + \
                                rfm_data['F'].astype(str) + \
                                rfm_data['M'].astype(str)

        self.rfm = rfm_data
        return self.rfm

    def segment_customers(self):
        """Segment customers based on their RFM scores"""
        def segment_logic(row):
            if row['R'] >= 4 and row['F'] >= 4 and row['M'] >= 4:
                return 'Champions'
            elif row['R'] >= 3 and row['F'] >= 3 and row['M'] >= 3:
                return 'Loyal'
            elif row['R'] >= 4 and row['F'] <= 2:
                return 'Recent'
            elif row['R'] >= 3 and row['F'] <= 2 and row['M'] <= 2:
                return 'Promising'
            elif row['R'] <= 2 and row['F'] >= 3 and row['M'] >= 3:
                return 'Attention'
            else:
                return 'Lost'

        self.rfm['Segment'] = self.rfm.apply(segment_logic, axis=1)
        self.rfm['Segment_Description'] = self.rfm['Segment'].map(self.segment_labels)
        return self.rfm

    def get_segment_summary(self):
        """Get summary statistics for each segment"""
        summary = self.rfm.groupby('Segment').agg({
            'recency': 'mean',
            'frequency': 'mean',
            'monetary': 'mean'
        }).round(2)
        
        # Add customer count
        summary['Customer_Count'] = self.rfm.groupby('Segment').size()
        
        summary.columns = ['Average Days', 'Average Frequency', 
                          'Average Monetary', 'Customer Count']
        return summary

    def get_results_df(self):
        """Get the final results DataFrame with all metrics and segments"""
        results = self.rfm.copy()
        results.reset_index(inplace=True)
        return results 