"""
Main Flask application for Massachusetts Recovery Services Directory
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import json
from typing import Dict, List
import os

app = Flask(__name__)

class RecoveryDirectoryApp:
    def __init__(self):
        self.data_file = 'data/recovery_services.csv'
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load recovery services data"""
        if os.path.exists(self.data_file):
            self.df = pd.read_csv(self.data_file)
        else:
            # Create empty DataFrame with standard columns
            columns = [
                'name', 'address', 'city', 'state', 'zip_code',
                'phone', 'email', 'website', 'service_types',
                'hours', 'populations_served', 'languages',
                'eligibility', 'payment_options', 'data_source'
            ]
            self.df = pd.DataFrame(columns=columns)
    
    def search_services(self, filters: Dict) -> List[Dict]:
        """Search services based on filters"""
        filtered_df = self.df.copy()
        
        # Apply filters
        if filters.get('zip_code'):
            filtered_df = filtered_df[filtered_df['zip_code'].str.contains(filters['zip_code'], na=False)]
        
        if filters.get('service_type'):
            filtered_df = filtered_df[filtered_df['service_types'].str.contains(filters['service_type'], na=False)]
        
        if filters.get('language'):
            filtered_df = filtered_df[filtered_df['languages'].str.contains(filters['language'], na=False)]
        
        if filters.get('population'):
            filtered_df = filtered_df[filtered_df['populations_served'].str.contains(filters['population'], na=False)]
        
        return filtered_df.to_dict('records')

directory_app = RecoveryDirectoryApp()

@app.route('/')
def index():
    """Main page with search interface"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Docker"""
    return jsonify({
        'status': 'healthy',
        'service': 'Massachusetts Recovery Services Directory',
        'version': '1.0.0'
    }), 200

@app.route('/api/search', methods=['POST'])
def search():
    """API endpoint for searching services"""
    filters = request.json
    results = directory_app.search_services(filters)
    return jsonify(results)

@app.route('/api/export', methods=['POST'])
def export_results():
    """Export search results to CSV"""
    filters = request.json
    results = directory_app.search_services(filters)
    
    if not results:
        return jsonify({'error': 'No results to export'}), 400
    
    # Create temporary CSV file
    temp_df = pd.DataFrame(results)
    temp_file = 'temp_export.csv'
    temp_df.to_csv(temp_file, index=False)
    
    return send_file(temp_file, as_attachment=True, download_name='recovery_services.csv')

@app.route('/api/stats')
def stats():
    """Get directory statistics"""
    total_services = len(directory_app.df)
    cities = directory_app.df['city'].nunique()
    service_types = directory_app.df['service_types'].str.split(',').explode().nunique()
    
    return jsonify({
        'total_services': total_services,
        'cities_covered': cities,
        'service_types': service_types
    })

if __name__ == '__main__':
    app.run(debug=True)