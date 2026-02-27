import re
import easyocr
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Optional


class InvoiceExtractor:
    """
    Extracts text and key information from invoice images using EasyOCR.
    """

    def __init__(self):
        # Initialize EasyOCR reader
        self.reader = easyocr.Reader(['en'], gpu=False)

    # ---------------- IMAGE PREPROCESSING ----------------
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Improve OCR accuracy using preprocessing.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Increase contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)

        return denoised

    # ---------------- TEXT EXTRACTION ----------------
    def extract_text(self, image_path: str) -> str:
        """
        Extract text from invoice image.
        """
        try:
            image = cv2.imread(image_path)

            if image is None:
                pil_image = Image.open(image_path)
                image = np.array(pil_image)

            processed = self.preprocess_image(image)

            results = self.reader.readtext(processed, detail=0)

            extracted_text = " ".join(results)

            return extracted_text.upper()

        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    # ---------------- GSTIN EXTRACTION ----------------
    def extract_gstin(self, text: str) -> Optional[str]:
        """
        Extract GSTIN using flexible regex.
        """
        # Remove spaces and handle OCR errors
        cleaned_text = text.replace(" ", "").replace("O", "0").replace("I", "1").replace("S", "5")
        
        # GSTIN pattern - more flexible
        gstin_patterns = [
            r'\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]',  # Standard
            r'GSTIN[:\s]*(\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d])',  # With GSTIN prefix
            r'(\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d])'  # Standalone
        ]
        
        for pattern in gstin_patterns:
            match = re.search(pattern, cleaned_text)
            if match:
                gstin = match.group(1) if match.groups() else match.group()
                # Validate and return
                if len(gstin) == 15:
                    return gstin
        
        return None

    # ---------------- DATE EXTRACTION ----------------
    def extract_invoice_date(self, text: str) -> Optional[str]:
        """
        Extract invoice date supporting multiple formats.
        """
        date_patterns = [
            r'DATE[:\s]*(\d{1,2}\s*[-/]\s*[A-Z]{3,}\s*[-/]\s*\d{4})',  # DATE: 23-JAN-2025
            r'\b(\d{1,2}\s*[-/]\s*[A-Z]{3,}\s*[-/]\s*\d{4})\b',      # 23-JAN-2025
            r'\b(\d{1,2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4})\b',       # 23-01-2025
            r'\b(\d{2}/\d{2}/\d{4})\b'                               # 23/01/2025
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date = match.group(1) if match.groups() else match.group()
                # Clean up the date format
                date = re.sub(r'\s+', '', date)  # Remove extra spaces
                date = re.sub(r'-+', '-', date)  # Fix multiple dashes
                return date.upper()
        
        return None

    # ---------------- TOTAL AMOUNT EXTRACTION ----------------
    def extract_total_amount(self, text: str) -> Optional[float]:
        """
        Extract total invoice amount intelligently.
        """
        # Look for TOTAL keyword first
        total_patterns = [
            r'(TOTAL|GRAND\s*TOTAL|GRAND\s*TOTAL).*?([\d,]+\.\d{2})',
            r'AMOUNT.*?([\d,]+\.\d{2})',
            r'₹\s*([\d,]+\.\d{2})',
            r'RS\s*([\d,]+\.\d{2})',
            r'INR\s*([\d,]+\.\d{2})'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(2) if match.groups() and len(match.groups()) > 1 else match.group(1)
                    amount = float(amount_str.replace(',', ''))
                    # Filter out very small amounts (likely not totals)
                    if amount > 10:
                        return amount
                except:
                    continue
        
        # Fallback: extract all decimal numbers and return the largest reasonable one
        numbers = re.findall(r'[\d,]+\.\d{2}', text)
        if numbers:
            try:
                amounts = [float(n.replace(',', '')) for n in numbers if float(n.replace(',', '')) > 10]
                if amounts:
                    return max(amounts)
            except:
                pass
        
        return None

    # ---------------- MAIN EXTRACTION FUNCTION ----------------
    def extract_invoice_info(self, image_path: str) -> Dict[str, any]:
        """
        Extract all invoice information.
        """
        extracted_text = self.extract_text(image_path)
        
        # Debug: Print extracted text
        print("🔍 DEBUG - Extracted Text:")
        print("=" * 50)
        print(extracted_text)
        print("=" * 50)
        
        gstin = self.extract_gstin(extracted_text)
        invoice_date = self.extract_invoice_date(extracted_text)
        total_amount = self.extract_total_amount(extracted_text)
        
        # Debug: Print extraction results
        print("📊 EXTRACTION RESULTS:")
        print(f"GSTIN: {gstin}")
        print(f"Date: {invoice_date}")
        print(f"Amount: {total_amount}")
        print("=" * 50)

        return {
            "extracted_text": extracted_text,
            "gstin": gstin,
            "invoice_date": invoice_date,
            "total_amount": total_amount
        }