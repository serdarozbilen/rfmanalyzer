import os
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
from werkzeug.utils import secure_filename
import plotly.express as px
import plotly.utils
import json
from rfm_analyzer import RFMAnalyzer

os.environ['FLASK_SKIP_DOTENV'] = '1'  # Skip loading .env file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload a CSV file'}), 400

    try:
        # Read the CSV file
        df = pd.read_csv(file)
        
        # Validate required columns
        required_columns = ['customer_id', 'transaction_date', 'transaction_amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            }), 400

        # Perform RFM analysis
        analyzer = RFMAnalyzer(df)
        analyzer.preprocess_data()
        analyzer.calculate_rfm_scores()
        analyzer.segment_customers()
        
        # Get results
        results = analyzer.get_results_df()
        summary = analyzer.get_segment_summary()
        
        # Format the summary table with better styling
        summary_html = summary.to_html(
            classes='table table-hover align-middle',
            float_format=lambda x: '{:,.2f}'.format(x) if isinstance(x, float) else x,
            justify='center',
            border=0,
            index_names=False,
            columns=['Average Days', 'Average Frequency', 'Average Monetary', 'Customer Count']
        ).replace('dataframe', 'table table-hover segment-table')
        
        # Create visualizations
        segment_dist = px.pie(
            results, 
            names='Segment', 
            title='Customer Segment Distribution',
            color='Segment',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        monetary_by_segment = px.box(
            results, 
            x='Segment', 
            y='monetary',
            title='Monetary Distribution by Segment'
        )
        
        # Convert plots to JSON
        plots = {
            'segment_dist': json.loads(json.dumps(segment_dist, cls=plotly.utils.PlotlyJSONEncoder)),
            'monetary_by_segment': json.loads(json.dumps(monetary_by_segment, cls=plotly.utils.PlotlyJSONEncoder))
        }
        
        # Save results to CSV
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], 'rfm_results.csv')
        results.to_csv(output_file, index=False)
        
        return render_template(
            'results.html',
            summary=summary_html,
            plots=plots
        )

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/download')
def download():
    output_file = os.path.join(app.config['UPLOAD_FOLDER'], 'rfm_results.csv')
    return send_file(
        output_file,
        mimetype='text/csv',
        as_attachment=True,
        download_name='rfm_results.csv'
    )

@app.route('/download_segment/<segment>')
def download_segment(segment):
    output_file = os.path.join(app.config['UPLOAD_FOLDER'], 'rfm_results.csv')
    
    try:
        # Read the full results
        df = pd.read_csv(output_file)
        
        # Filter for the requested segment
        segment_df = df[df['Segment'].str.lower() == segment.lower()]
        
        if segment_df.empty:
            return jsonify({'error': f'No customers found in {segment} segment'}), 404
        
        # Save segment-specific results
        segment_file = os.path.join(app.config['UPLOAD_FOLDER'], f'rfm_results_{segment}.csv')
        segment_df.to_csv(segment_file, index=False)
        
        return send_file(
            segment_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'rfm_results_{segment}.csv'
        )
    except Exception as e:
        return jsonify({'error': f'Error processing segment download: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000) 