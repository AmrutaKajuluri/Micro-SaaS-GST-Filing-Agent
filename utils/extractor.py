
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

        # Remove spaces (OCR may split GSTIN)
        cleaned_text = text.replace(" ", "")

        gstin_pattern = r'\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]'

        match = re.search(gstin_pattern, cleaned_text)

        if match:
            return match.group()

        return None

    # ---------------- DATE EXTRACTION ----------------
    def extract_invoice_date(self, text: str) -> Optional[str]:
        """
        Extract invoice date supporting multiple formats.
        """

        date_patterns = [
            r'\b\d{1,2}\s*[-/]\s*[A-Z]{3}\s*[-/]\s*\d{4}\b',   # 23 - JAN - 2025
            r'\b\d{1,2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4}\b',    # 23-01-2025
            r'\b\d{2}/\d{2}/\d{4}\b'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()

        return None

    # ---------------- TOTAL AMOUNT EXTRACTION ----------------
    def extract_total_amount(self, text: str) -> Optional[float]:
        """
        Extract total invoice amount intelligently.
        """

        # Look for TOTAL keyword first
        total_match = re.search(r'(TOTAL|GRANDTOTAL|GRAND TOTAL).*?([\d,]+\.\d{2})', text)

        if total_match:
            try:
                return float(total_match.group(2).replace(',', ''))
            except:
                pass

        # Fallback: extract all decimal numbers and return max
        numbers = re.findall(r'[\d,]+\.\d{2}', text)

        if numbers:
            try:
                amounts = [float(n.replace(',', '')) for n in numbers]
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

        gstin = self.extract_gstin(extracted_text)
        invoice_date = self.extract_invoice_date(extracted_text)
        total_amount = self.extract_total_amount(extracted_text)

        return {
            "extracted_text": extracted_text,
            "gstin": gstin,
            "invoice_date": invoice_date,
            "total_amount": total_amount
        }