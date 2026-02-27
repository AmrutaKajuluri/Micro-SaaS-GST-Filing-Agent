# AI GST Filing Agent for Kirana Stores

A modern Micro-SaaS application that automates GST invoice processing for small businesses using AI and OCR technology with a beautiful React frontend.

## Features

- 📤 **Modern Invoice Upload**: Drag & drop interface with image preview
- 🔍 **AI-Powered OCR**: Uses EasyOCR to extract text from invoices
- 🧾 **Smart GST Extraction**: Automatically extracts:
  - GSTIN (with regex validation)
  - Invoice date
  - Total invoice amount
- 💰 **Intelligent GST Calculation**: 
  - Applies 18% standard GST rate
  - For Andhra Pradesh (state code 37): CGST 9% + SGST 9%
  - For other states: IGST 18%
- 📊 **Beautiful Dashboard**: Modern React UI with real-time results
- 📋 **GSTR-1 Generation**: Creates draft CSV with required columns
- 💾 **One-Click CSV Export**: Download GSTR-1 ready CSV file

## Architecture

```
Micro-SaaS-GST-Filing-Agent/
├── api_server.py          # Flask REST API server
├── app.py                 # Original Streamlit app (backup)
├── start.py              # Unified startup script
├── requirements.txt       # Python dependencies
├── frontend/             # React frontend application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── App.js       # Main app component
│   │   └── index.js     # Entry point
│   ├── public/
│   └── package.json     # Node.js dependencies
├── utils/
│   ├── extractor.py      # OCR and text extraction logic
│   └── gst_logic.py      # GST validation and calculation logic
└── README.md             # This file
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Micro-SaaS-GST-Filing-Agent
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install frontend dependencies:**
```bash
cd frontend
npm install
cd ..
```

### Running the Application

#### Option 1: Easy Start (Recommended)
```bash
python start.py
```
This will automatically:
- Start the Flask API server (port 5000)
- Start the React frontend (port 3000)
- Open your browser to `http://localhost:3000`

#### Option 2: Manual Start
```bash
# Terminal 1: Start API server
python api_server.py

# Terminal 2: Start frontend
cd frontend
npm start
```

#### Option 3: Streamlit Version (Legacy)
```bash
streamlit run app.py
```

## Usage

1. Open your browser to `http://localhost:3000`
2. **Upload Invoice**: Drag & drop or browse to select your invoice image (JPG/PNG)
3. **Process**: Click "Extract GST Information" to process with AI
4. **Review**: Check the extracted GST information and calculations
5. **Download**: Click "Download GSTR-1 CSV" to get your filing-ready file

## Frontend Features

### Modern UI Components
- **Drag & Drop Upload**: Intuitive file upload with preview
- **Real-time Processing**: Live status updates during extraction
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Beautiful Dashboard**: Clean, modern interface with Tailwind CSS

### Key Components
- `InvoiceUpload`: Handles file upload and preview
- `GSTResults`: Displays extracted information and calculations
- `Header/Footer`: Professional branding and navigation
- `GSTResults`: Comprehensive results display with CSV download

## API Endpoints

### `GET /api/health`
Health check endpoint

### `POST /api/process-invoice`
Process invoice image and extract GST information
- **Request**: multipart/form-data with file field
- **Response**: JSON with extracted data and GST calculations

### `POST /api/download-csv`
Download GSTR-1 CSV file
- **Request**: JSON with GSTR-1 data
- **Response**: CSV file download

## GST Logic Explanation

### Tax Structure
- **Standard GST Rate**: 18% (applicable to most goods)
- **Intra-state transactions** (Andhra Pradesh - state code 37):
  - CGST: 9%
  - SGST: 9%
- **Inter-state transactions** (other states):
  - IGST: 18%

### Calculation Formula
```
Taxable Value = Invoice Amount ÷ (1 + GST Rate)
GST Amount = Invoice Amount - Taxable Value
```

### GSTIN Validation
GSTIN format: `2 digits (state code) + 10 characters (PAN) + 1 digit + 1 character + 1 character (Z)`

Example: `37AAAPL1234C1ZV` (Andhra Pradesh)

## Dependencies

### Backend
- **Flask**: REST API framework
- **Flask-CORS**: Cross-origin resource sharing
- **EasyOCR**: Optical Character Recognition
- **OpenCV**: Image processing
- **Pandas**: CSV generation and data manipulation
- **Pillow**: Image handling
- **NumPy**: Numerical operations

### Frontend
- **React**: Modern UI framework
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API calls
- **React Dropzone**: File upload component
- **Lucide React**: Modern icon library

## Development

### Backend Development
```bash
# Start API server only
python api_server.py
```

### Frontend Development
```bash
cd frontend
npm start
```

### Building for Production
```bash
cd frontend
npm run build
```

## Notes

- This tool uses AI/OCR for text extraction. Accuracy depends on image quality.
- Always verify extracted information before GST filing.
- GST rates and rules may vary based on product categories and applicable laws.
- This is a simplified implementation suitable for demonstration purposes.

## Troubleshooting

### Common Issues

1. **Port already in use**: Change ports in `api_server.py` or React configuration
2. **OCR not working**: Ensure EasyOCR models are downloaded (first run may take time)
3. **CORS errors**: API server should handle these with Flask-CORS
4. **Image upload fails**: Check file size and format (JPG/PNG only)

### Performance Tips
- Use clear, high-resolution invoice images
- Ensure good lighting and minimal shadows in invoice photos
- For batch processing, consider implementing queue management

## Disclaimer

This application assists with GST filing processes but should not be considered as legal or financial advice. Always consult with a qualified GST professional for accurate filing and compliance.
