from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io
import tempfile
import os
from PIL import Image
from utils.extractor import InvoiceExtractor
from utils.gst_logic import GSTLogic

app = Flask(__name__)
CORS(app)

# Initialize classes
extractor = InvoiceExtractor()
gst_logic = GSTLogic()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "GST API Server is running"})

@app.route('/api/process-invoice', methods=['POST'])
def process_invoice():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check file extension
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return jsonify({"error": "Invalid file format. Please upload JPG or PNG"}), 400
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            file.save(tmp_file.name)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract information
            invoice_info = extractor.extract_invoice_info(tmp_file_path)
            
            # Process with GST logic
            processed_data = gst_logic.process_invoice(invoice_info)
            
            # Prepare response
            response = {
                "success": True,
                "invoice_info": invoice_info,
                "processed_data": processed_data,
                "gstr1_data": processed_data['gstr1_row']
            }
            
            return jsonify(response)
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        return jsonify({"error": f"Error processing invoice: {str(e)}"}), 500

@app.route('/api/download-csv', methods=['POST'])
def download_csv():
    try:
        data = request.json
        if not data or 'gstr1_data' not in data:
            return jsonify({"error": "No GSTR-1 data provided"}), 400
        
        # Create DataFrame
        df = pd.DataFrame([data['gstr1_data']])
        
        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Generate filename
        gstin = data.get('gstin', 'invoice')
        invoice_date = data.get('invoice_date', 'date')
        filename = f"GSTR-1_{gstin}_{invoice_date}.csv"
        
        # Create file-like object
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        
        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({"error": f"Error generating CSV: {str(e)}"}), 500

if __name__ == '__main__':
    print("Starting GST API Server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
