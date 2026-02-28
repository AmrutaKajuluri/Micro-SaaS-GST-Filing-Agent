import re
import os
import io
import fitz # PyMuPDF
from pdf2image import convert_from_path
import easyocr
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Optional, Any


class InvoiceExtractor:
    """
    Extracts text and key information from invoice images or PDFs.
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
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from invoice (supports Image or PDF via Hybrid strategy).
        """
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # --- PDF HANDLING (Hybrid Approach) ---
            if ext == '.pdf':
                # 1. Attempt Native PDF Text Extraction (PyMuPDF)
                doc = fitz.open(file_path)
                native_text = ""
                for page in doc:
                    native_text += page.get_text() + " "
                doc.close()
                
                # If we successfully extracted enough pure text (e.g. Tally/Stripe PDF)
                if len(native_text.strip()) > 50:
                    print("✅ Skipped OCR: Extracted text natively from PDF.")
                    return native_text.upper()
                
                # 2. Fallback to OCR for Scanned PDFs
                print("⚠️ Scanned PDF detected (no native text). Falling back to OCR.")
                extracted_text = ""
                
                # Convert PDF pages to PIL Images
                # Note: poppler must be installed on the system, otherwise this will fail
                pages = convert_from_path(file_path, dpi=300)
                
                for page_img in pages:
                    # Convert PIL image to numpy array for OpenCV/EasyOCR
                    img_array = np.array(page_img)
                    # Convert RGB to BGR (OpenCV default)
                    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    
                    processed = self.preprocess_image(img_array)
                    results = self.reader.readtext(processed, detail=0)
                    extracted_text += " ".join(results) + " "
                
                return extracted_text.upper()

            # --- STANDARD IMAGE HANDLING (JPG/PNG) ---
            else:
                image = cv2.imread(file_path)

                if image is None:
                    pil_image = Image.open(file_path)
                    image = np.array(pil_image)
                    if len(image.shape) == 3 and image.shape[2] == 3:
                        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                processed = self.preprocess_image(image)
                results = self.reader.readtext(processed, detail=0)
                extracted_text = " ".join(results)

                return extracted_text.upper()

        except Exception as e:
            print(f"Extraction Error: {e}")
            return ""

    # ---------------- GSTIN EXTRACTION ----------------
    def extract_gstin(self, text: str) -> Optional[str]:
        """
        Extract GSTIN using highly flexible OCR-tolerant logical window.
        """
        # We strip ALL spaces and punctuation to find the pure sequence
        cleaned_text = re.sub(r'[^A-Za-z0-9]', '', text).upper()
        
        candidates = []
        
        # Look for 15-char and 14-char windows (in case 'Z' is dropped)
        # We need to be very aggressive with substitutions due to heavy OCR artifacting
        for length in [15, 14]:
            for i in range(len(cleaned_text) - length + 1):
                raw = cleaned_text[i:i+length]
                
                # 1. State Code (indices 0-1) - MUST be digits
                state_code = raw[0:2].replace('O','0').replace('I','1').replace('S','5').replace('Z','2').replace('G','6').replace('B','8').replace('T','7')
                if not (state_code.isdigit() and 1 <= int(state_code) <= 38): continue
                
                # 2. PAN Letters (indices 2-6) - MUST be letters
                pan_letters = raw[2:7].replace('0','O').replace('1','I').replace('5','S').replace('8','B').replace('2','Z').replace('6','G').replace('7','T')
                if not pan_letters.isalpha(): continue
                # Block obvious false positives formed by stripping spaces
                if pan_letters in ['PHONE', 'EMAIL', 'TOTAL', 'GRAND', 'STATE', 'INDIA']: continue
                
                # 3. PAN Digits (indices 7-10) - MUST be digits
                pan_digits = raw[7:11].replace('O','0').replace('I','1').replace('S','5').replace('Z','2').replace('B','8').replace('G','6').replace('T','7')
                if not pan_digits.isdigit(): continue
                
                # 4. PAN Last Letter (index 11) - MUST be letter
                pan_last = raw[11:12].replace('0','O').replace('1','I').replace('5','S').replace('8','B').replace('2','Z').replace('6','G').replace('7','T')
                if not pan_last.isalpha(): continue
                
                # 5. Entity Code (index 12) - alphanumeric, usually '1'
                entity_code = raw[12:13].replace('I', '1').replace('O', '0')
                
                # 6 & 7. 'Z' and Checksum
                if length == 15:
                    z_char = raw[13:14]
                    if z_char not in 'Z25SO0I1': continue
                    checksum = raw[14:15]
                else:
                    checksum = raw[13:14]
                    
                gstin = f"{state_code}{pan_letters}{pan_digits}{pan_last}{entity_code}Z{checksum}"
                
                # Score the candidate based on proximity to the word "GSTIN" or "GST" in the original text
                # We can do this simply by checking if it exists near "GST"
                candidates.append({
                    "gstin": gstin,
                    "index": i,
                    "length": length
                })
                
        if candidates:
            # Sort candidates by length (prefer 15 over 14), then by appearance
            candidates.sort(key=lambda x: (-x['length'], x['index']))
            return candidates[0]['gstin']
                
        return None

    # ---------------- DATE EXTRACTION ----------------
    def extract_invoice_date(self, text: str) -> Optional[str]:
        """
        Extract invoice date supporting multiple formats and OCR artifacts.
        """
        date_patterns = [
            r'(?:DATE|DT)[:\s\-\.]*(\d{1,2}[\s\-\./]+[A-Za-z]{3,}[\s\-\./]+[0-9A-Za-z]{2,4})',
            r'\b(\d{1,2}[\s\-\./]+[A-Za-z]{3,}[\s\-\./]+[0-9A-Za-z]{2,4})\b',
            r'\b(\d{1,2}[\s\-\./]+\d{1,2}[\s\-\./]+[0-9A-Za-z]{2,4})\b',
            r'(?:DATE|DT)[\s\-\.]*(\d{1,2}[\s\-\./]+\d{1,2}[\s\-\./]+[0-9A-Za-z]{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date = match.group(1).upper()
                
                # Standardize separators to '-'
                date = re.sub(r'[\s\./]+', '-', date)
                
                # Fix common OCR artifacts in years (e.g. 202S -> 2025)
                parts = date.split('-')
                if len(parts) == 3:
                    # Clean the year strictly
                    year = parts[2].replace('S', '5').replace('O', '0').replace('I', '1').replace('Z', '2').replace('B','8').replace('G','6')
                    # Fix 2-digit years if applicable
                    if len(year) == 2:
                        year = "20" + year
                    
                    # Clean the month strictly if it's supposed to be numbers
                    month = parts[1].replace('O', '0').replace('I', '1').replace('S', '5')
                    
                    # Clean the day strictly
                    day = parts[0].replace('O', '0').replace('I', '1').replace('S', '5')
                    
                    date = f"{day}-{month}-{year}"
                    
                return date
                
        # Super degraded fallback: look for `DD MM YYYY` anywhere physically close to the word "DATE"
        # Example from user image: "02 2025 DELH: 0MEREIUT SHARNII KIRANA STORC..." where "15/03/2025" got completely mangled into "02 2025"
        # Since it's too degraded, we might not always get it. But let's try a fallback for standard formats at least
        fallback_pattern = r'(\d{2}[\s\-\./]+\d{2}[\s\-\./]+202\d)'
        match = re.search(fallback_pattern, text)
        if match:
            date = match.group(1).upper()
            date = re.sub(r'[\s\./]+', '-', date)
            return date
        
        return None

    # ---------------- TOTAL AMOUNT EXTRACTION ----------------
    def extract_total_amount(self, text: str) -> Optional[float]:
        """
        Extract total invoice amount by searching for keywords and then 
        inspecting the immediate neighborhood for a valid currency format.
        """
        import re

        def clean_amt(s: str) -> float:
            # Remove everything except digits and dot
            clean_str = re.sub(r'[^0-9.]', '', s.replace(',', ''))
            try:
                # If there are multiple dots, take the last one as decimal
                if clean_str.count('.') > 1:
                    parts = clean_str.split('.')
                    clean_str = "".join(parts[:-1]) + "." + parts[-1]
                return float(clean_str)
            except ValueError:
                return 0.0

        # Patterns to find numbers that look like totals (digits with possible 2-decimal places)
        # Supports Indian grouping (e.g. 1,05,200.00) and Western grouping (e.g. 105,200.00)
        # The logic: matches strings of digits and commas, optionally ending with .xx
        amount_regex = re.compile(r'(?<!\d)(?:\d[,]?)+\.\d{2}(?!\d)')

        def find_best_amount_in_window(window: str) -> Optional[float]:
            # Find all numbers in the window
            matches = amount_regex.findall(window)
            valid_amts = []
            for m in matches:
                val = clean_amt(m)
                # Ignore values too small or those that look like HSN numbers
                if 10 < val < 10000000: # 1 Crore limit
                    valid_amts.append(val)
            
            # If multiple numbers exist in the window (e.g. "Total 1,05,200.00 balance 5,200.00")
            # We assume the LARGEST one is the actual Total
            return max(valid_amts) if valid_amts else None

        # Priority 1: Grand Total keywords (usually unique and at the bottom)
        grand_total_keywords = [r'GRAND\s*TOTAL', r'TOTAL\s*PAYABLE', r'NET\s*AMOUNT', r'PAYABLE\s*AMOUNT', r'TOTAL\s*DUE']
        for kw in grand_total_keywords:
            matches = list(re.finditer(kw, text, re.IGNORECASE))
            if matches:
                # Take the last one
                match = matches[-1]
                # Look at the 60 characters following the keyword
                window = text[match.end():match.end()+100]
                amt = find_best_amount_in_window(window)
                if amt: return amt

        # Priority 2: Generic "Total"
        # We use word boundaries to avoid matching "Total Sale" or "Total Tax"
        total_matches = list(re.finditer(r'\bTOTAL\b', text, re.IGNORECASE))
        if total_matches:
            for match in reversed(total_matches):
                window = text[match.end():match.end()+100]
                # Skip if window contains "Tax" or "Sale" immediately
                if re.search(r'^\s*(?:TAX|SALE|QTY|UNIT|PRICE)', window, re.IGNORECASE):
                    continue
                amt = find_best_amount_in_window(window)
                if amt: return amt

        # Priority 3: "Amount" or "Amt" - more restrictive context
        amt_keywords = [r'\bAMOUNT\b', r'\bAMT\b']
        for kw in amt_keywords:
            matches = list(re.finditer(kw, text, re.IGNORECASE))
            if matches:
                for match in reversed(matches):
                    # For "Amount", we check if it's likely a header by looking for siblings
                    window_before = text[max(0, match.start()-50):match.start()]
                    if "HSN" in window_before or "Qty" in window_before or "Description" in window_before:
                        continue # Skip table header
                    
                    window = text[match.end():match.end()+100]
                    amt = find_best_amount_in_window(window)
                    if amt: return amt

        # Fallback: Just find the largest number in the last 30% of the document
        end_text = text[-int(len(text)*0.3):] if len(text) > 100 else text
        amounts = []
        for m in amount_regex.findall(end_text):
            val = clean_amt(m)
            if 10 < val < 10000000 and '.' in m: # Require decimal for fallback confidence
                amounts.append(val)
        
        return max(amounts) if amounts else None

    # ---------------- MAIN EXTRACTION FUNCTION ----------------
    def extract_invoice_info(self, image_path: str) -> Dict[str, Any]:
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