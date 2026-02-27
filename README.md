# AI GST Filing Agent for Kirana Stores

A Micro-SaaS application that automates GST invoice processing for small businesses using AI and OCR technology.

## Features

- 📤 **Invoice Upload**: Upload invoice images (JPG/PNG)
- 🔍 **OCR Extraction**: Uses EasyOCR to extract text from invoices
- 🧾 **GST Information Extraction**: Automatically extracts:
  - GSTIN (using regex validation)
  - Invoice date
  - Total invoice amount
- 💰 **GST Tax Calculation**: 
  - Applies 18% standard GST rate
  - For Andhra Pradesh (state code 37): CGST 9% + SGST 9%
  - For other states: IGST 18%
- 📊 **GSTR-1 Generation**: Creates draft CSV with required columns:
  - GSTIN/UIN of Recipient
  - Invoice Date
  - Invoice Value
  - Place of Supply
  - Reverse Charge
  - Invoice Type
- 💾 **CSV Export**: Download GSTR-1 ready CSV file

## Project Structure

```
Micro-SaaS-GST-Filing-Agent/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── utils/
    ├── extractor.py      # OCR and text extraction logic
    └── gst_logic.py      # GST validation and calculation logic
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Micro-SaaS-GST-Filing-Agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit application:
```bash
streamlit run app.py
```

2. Open your browser and go to `http://localhost:8501`

3. Upload your invoice image and click "Extract GST Information"

4. Review the extracted data and download the GSTR-1 CSV file

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

- **Streamlit**: Web application framework
- **EasyOCR**: Optical Character Recognition
- **OpenCV**: Image processing
- **Pandas**: CSV generation and data manipulation
- **Pillow**: Image handling
- **NumPy**: Numerical operations

## Notes

- This tool uses AI/OCR for text extraction. Accuracy depends on image quality.
- Always verify extracted information before GST filing.
- GST rates and rules may vary based on product categories and applicable laws.
- This is a simplified implementation suitable for demonstration purposes.

## Disclaimer

This application assists with GST filing processes but should not be considered as legal or financial advice. Always consult with a qualified GST professional for accurate filing and compliance.
