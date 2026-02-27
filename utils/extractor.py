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
        # Initialize EasyOCR reader for English
        self.reader = easyocr.Reader(['en'])
        
        # GSTIN regex pattern (15 characters: 2 digits + [A-Z]{5} + 4 digits + [A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1})
        self.gstin_pattern = r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1}\b'
        
        # Date patterns (DD-MM-YYYY, DD/MM/YYYY, etc.)
        self.date_patterns = [
            r'\b\d{2}[-/]\d{2}[-/]\d{4}\b',  # DD-MM-YYYY or DD/MM/YYYY
            r'\b\d{2}[-/]\d{2}[-/]\d{2}\b',   # DD-MM-YY or DD/MM/YY
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b'  # D-M-YYYY or D/M/YYYY
        ]
        
        # Amount patterns (looking for total amounts)
        self.amount_patterns = [
            r'Total.*?[:\s]*₹?\s*([\d,]+\.?\d*)',
            r'Grand Total.*?[:\s]*₹?\s*([\d,]+\.?\d*)',
            r'Amount.*?[:\s]*₹?\s*([\d,]+\.?\d*)',
            r'₹\s*([\d,]+\.?\d*)',
            r'INR\s*([\d,]+\.?\d*)'
        ]
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply threshold to get better text contrast
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised
    
    def extract_text(self, image_path: str) -> str:
        """
        Extract text from invoice image using EasyOCR.
        """
        try:
            # Read and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                # Try with PIL if OpenCV fails
                pil_image = Image.open(image_path)
                image = np.array(pil_image)
            
            processed_image = self.preprocess_image(image)
            
            # Extract text using EasyOCR
            results = self.reader.readtext(processed_image)
            
            # Combine all detected text
            extracted_text = ' '.join([result[1] for result in results])
            
            return extracted_text.upper()  # Convert to uppercase for better pattern matching
            
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    def extract_gstin(self, text: str) -> Optional[str]:
        """
        Extract GSTIN from extracted text using regex.
        """
        matches = re.findall(self.gstin_pattern, text)
        return matches[0] if matches else None
    
    def extract_invoice_date(self, text: str) -> Optional[str]:
        """
        Extract invoice date from extracted text.
        """
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Look for dates near "Date", "Invoice Date", etc.
                for match in matches:
                    # Check if date is near date-related keywords
                    date_context = re.search(r'(DATE|INVOICE.*?DATE|BILL.*?DATE).*?([0-9]{2}[-/][0-9]{2}[-/][0-9]{2,4})', text)
                    if date_context:
                        return date_context.group(2)
                    return match
        return None
    
    def extract_total_amount(self, text: str) -> Optional[float]:
        """
        Extract total invoice amount from extracted text.
        """
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Clean amount string and convert to float
                    amount_str = matches[-1].replace(',', '').replace(' ', '')
                    return float(amount_str)
                except ValueError:
                    continue
        
        # Fallback: look for any large number that could be total
        numbers = re.findall(r'\b[\d,]+\.\d{2}\b', text)
        if numbers:
            try:
                # Return the largest number (likely the total)
                amounts = [float(num.replace(',', '')) for num in numbers]
                return max(amounts)
            except ValueError:
                pass
        
        return None
    
    def extract_invoice_info(self, image_path: str) -> Dict[str, any]:
        """
        Extract all invoice information from image.
        """
        # Extract text from image
        extracted_text = self.extract_text(image_path)
        
        # Extract specific information
        gstin = self.extract_gstin(extracted_text)
        invoice_date = self.extract_invoice_date(extracted_text)
        total_amount = self.extract_total_amount(extracted_text)
        
        return {
            'extracted_text': extracted_text,
            'gstin': gstin,
            'invoice_date': invoice_date,
            'total_amount': total_amount
        }
