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
        Extract total invoice amount intelligently from deeply nested or corrupted strings.
        """
        # Look for explicit Total keywords + amounts nearby (handling spaces/corrupted chars)
        # Note: Added `\s*` before the dot and inside digits in case OCR splits number 123.45 into 123 . 45
        total_patterns = [
            r'(?:TOTAL|GRAND\s*TOTAL|GRANDTOTAL|NET\s*AMOUNT|AMT).*?([\d\s,]+\s*\.\s*\d{2})',
            r'AMOUNT.*?([\d\s,]+\s*\.\s*\d{2})',
            r'[₹₹RSINR]\s*([\d\s,]+\s*\.\s*\d{2})'
        ]
        
        all_amounts = []
        
        # Helper to clean spaced amounts
        def clean_amt(s: str) -> float:
            # First remove commas, then merge spaces if they act as separators implicitly
            clean_str = re.sub(r'[,]', '', s).strip()
            # If there's a space before the last two digits and no dot, assume it's a mangled decimal e.g. "968 00"
            if '.' not in clean_str and ' ' in clean_str:
                parts = clean_str.split(' ')
                if len(parts[-1]) == 2:
                    clean_str = "".join(parts[:-1]) + "." + parts[-1]
            # Strip remaining spaces
            return float(re.sub(r'[\s]', '', clean_str))
        
        # 1. First pass: explicit keyword matching
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(2) if match.groups() and len(match.groups()) > 1 else match.group(1)
                    amount = clean_amt(amount_str)
                    if amount > 10:
                        all_amounts.append(amount)
                except:
                    continue
        
        # 2. Second pass: aggressive floating point extraction towards the end of document
        # Most totals exist in the last 20% of the text.
        end_text_segment = text[-int(len(text)*0.3):]
        numbers = re.findall(r'[\d\s,]+\s*\.\s*\d{2}', end_text_segment)
        if numbers:
            for n in numbers:
                try:
                    amt = clean_amt(n)
                    if amt > 10:
                        all_amounts.append(amt)
                except:
                    pass
                    
        # 3. Third pass: aggregate all floating numbers in document
        if not all_amounts:
            numbers = re.findall(r'[\d,]+\.\d{2}', text)
            if numbers:
                for n in numbers:
                    try:
                        amt = clean_amt(n)
                        if amt > 10:
                            all_amounts.append(amt)
                    except:
                        pass
                        
        # 4. Super aggressive fallback: find space-separated numbers like "968 00" next to "TOTAL"
        fallback_pattern = r'(?:TOTAL|GRAND\s+TOTAL)\s+[^\d]*(\d+)\s+(\d{2})\b'
        match = re.search(fallback_pattern, text, re.IGNORECASE)
        if match:
            all_amounts.append(float(f"{match.group(1)}.{match.group(2)}"))
            
        # 5. Deal with extreme OCR symbol injections separating TOTAL from Amount like "GRANDTOTAL {19,854.X0"
        emergency_pattern = r'(?:TOTAL|GRANDTOTAL).*?([\d,]{2,})[\.\sX]*(\d{2})'
        match = re.search(emergency_pattern, text, re.IGNORECASE)
        if match:
             amt = float(f"{match.group(1).replace(',','')}.{match.group(2)}")
             if amt > 10: all_amounts.append(amt)
        
        if all_amounts:
            # Safely assume the MAX number found in a document typically represents the Total
            return max(all_amounts)
            
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