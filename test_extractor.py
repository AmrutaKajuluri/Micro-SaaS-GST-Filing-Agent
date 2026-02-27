import re
from typing import Optional

def extract_gstin(text: str) -> Optional[str]:
    cleaned_text = re.sub(r'[^A-Za-z0-9]', '', text).upper()
    for length in [15, 14]:
        for i in range(len(cleaned_text) - length + 1):
            raw = cleaned_text[i:i+length]
            state_code = raw[0:2].replace('O','0').replace('I','1').replace('S','5')
            if not (state_code.isdigit() and 1 <= int(state_code) <= 38): continue
            pan_letters = raw[2:7].replace('0','O').replace('1','I').replace('5','S')
            if not pan_letters.isalpha(): continue
            pan_digits = raw[7:11].replace('O','0').replace('I','1').replace('5','S').replace('Z','2').replace('B','8')
            if not pan_digits.isdigit(): continue
            pan_last = raw[11:12].replace('0','O').replace('1','I').replace('5','S')
            if not pan_last.isalpha(): continue
            entity_code = raw[12:13]
            if length == 15:
                z_char = raw[13:14]
                if z_char not in 'Z25SO0I1': continue
                checksum = raw[14:15]
            else:
                checksum = raw[13:14]
            return f"{state_code}{pan_letters}{pan_digits}{pan_last}{entity_code}Z{checksum}"
    return None

def extract_invoice_date(text: str) -> Optional[str]:
    date_patterns = [
        r'DATE[:\s\-\.]*(\d{1,2}[\s\-\./]+[A-Za-z]{3,}[\s\-\./]+[0-9A-Za-z]{2,4})',
        r'\b(\d{1,2}[\s\-\./]+[A-Za-z]{3,}[\s\-\./]+[0-9A-Za-z]{2,4})\b',
        r'\b(\d{1,2}[\s\-\./]+\d{1,2}[\s\-\./]+[0-9A-Za-z]{2,4})\b'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date = match.group(1).upper()
            date = re.sub(r'[\s\./]+', '-', date)
            parts = date.split('-')
            if len(parts) == 3:
                year = parts[2].replace('S', '5').replace('O', '0').replace('I', '1').replace('Z', '2')
                if len(year) == 2: year = "20" + year
                date = f"{parts[0]}-{parts[1]}-{year}"
            return date
    return None

def extract_total_amount(text: str) -> Optional[float]:
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
                if amount > 10: return amount
            except: continue
    
    numbers = re.findall(r'[\d,]+\.\d{2}', text)
    if numbers:
        try:
            amounts = [float(n.replace(',', '')) for n in numbers if float(n.replace(',', '')) > 10]
            if amounts: return max(amounts)
        except: pass
    return None

ocr_texts = [
    # Invoice 1
    "DATE: 12-JAN-2025 GSTIN: 27AABCB1234D1Z5 TOTAL 1500.00",
    # Invoice 2 - OCR errors
    "INvOICE DATE 23 01 202S G5TIN: 37AAPPL1234C1ZV AMOUNT: RS 12000.50",
    # Invoice 3 - OCR errors
    "D A T E : 14.12.2024 GSTIN 07SGHPS1234Z2E TOTAL 500.00"
]

for i, text in enumerate(ocr_texts):
    print(f"\n--- Testing Invoice {i+1} ---")
    gstin = extract_gstin(text)
    date = extract_invoice_date(text)
    amount = extract_total_amount(text)
    print(f"Extracted GSTIN: {gstin}")
    print(f"Extracted Date : {date}")
    print(f"Extracted Amt  : {amount}")
