import sys
import re
from typing import Optional

def extract_gstin(text: str) -> Optional[str]:
    cleaned_text = re.sub(r'[^A-Za-z0-9]', '', text).upper()
    candidates = []
    
    for length in [15, 14]:
        for i in range(len(cleaned_text) - length + 1):
            raw = cleaned_text[i:i+length]
            state_code = raw[0:2].replace('O','0').replace('I','1').replace('S','5').replace('Z','2').replace('G','6').replace('B','8').replace('T','7')
            if not (state_code.isdigit() and 1 <= int(state_code) <= 38): continue
            
            pan_letters = raw[2:7].replace('0','O').replace('1','I').replace('5','S').replace('8','B').replace('2','Z').replace('6','G').replace('7','T')
            if not pan_letters.isalpha(): continue
            if pan_letters in ['PHONE', 'EMAIL', 'TOTAL', 'GRAND', 'STATE', 'INDIA']: continue
            
            pan_digits = raw[7:11].replace('O','0').replace('I','1').replace('S','5').replace('Z','2').replace('B','8').replace('G','6').replace('T','7')
            if not pan_digits.isdigit(): continue
            
            pan_last = raw[11:12].replace('0','O').replace('1','I').replace('5','S').replace('8','B').replace('2','Z').replace('6','G').replace('7','T')
            if not pan_last.isalpha(): continue
            
            entity_code = raw[12:13].replace('I', '1').replace('O', '0')
            if length == 15:
                z_char = raw[13:14]
                if z_char not in 'Z25SO0I1': continue
                checksum = raw[14:15]
            else:
                checksum = raw[13:14]
                
            gstin = f"{state_code}{pan_letters}{pan_digits}{pan_last}{entity_code}Z{checksum}"
            
            candidates.append({
                "gstin": gstin,
                "index": i,
                "length": length
            })
            
    if candidates:
        candidates.sort(key=lambda x: (-x['length'], x['index']))
        return candidates[0]['gstin']
            
    return None

def extract_invoice_date(text: str) -> Optional[str]:
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
            date = re.sub(r'[\s\./]+', '-', date)
            parts = date.split('-')
            if len(parts) == 3:
                year = parts[2].replace('S', '5').replace('O', '0').replace('I', '1').replace('Z', '2').replace('B','8').replace('G','6')
                if len(year) == 2: year = "20" + year
                month = parts[1].replace('O', '0').replace('I', '1').replace('S', '5')
                day = parts[0].replace('O', '0').replace('I', '1').replace('S', '5')
                date = f"{day}-{month}-{year}"
            return date
    fallback_pattern = r'(\d{2}[\s\-\./]+\d{2}[\s\-\./]+202\d)'
    match = re.search(fallback_pattern, text)
    if match:
        date = match.group(1).upper()
        date = re.sub(r'[\s\./]+', '-', date)
        return date
    return None

def extract_total_amount(text: str) -> Optional[float]:
    total_patterns = [
        r'(?:TOTAL|GRAND\s*TOTAL|GRANDTOTAL|NET\s*AMOUNT|AMT).*?([\d\s,]+\s*\.\s*\d{2})',
        r'AMOUNT.*?([\d\s,]+\s*\.\s*\d{2})',
        r'[₹₹RSINR]\s*([\d\s,]+\s*\.\s*\d{2})'
    ]
    all_amounts = []
    
    def clean_amt(s: str) -> float:
        clean_str = re.sub(r'[,]', '', s).strip()
        if '.' not in clean_str and ' ' in clean_str:
            parts = clean_str.split(' ')
            if len(parts[-1]) == 2:
                clean_str = "".join(parts[:-1]) + "." + parts[-1]
        return float(re.sub(r'[\s]', '', clean_str))
    
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(2) if match.groups() and len(match.groups()) > 1 else match.group(1)
                amount = clean_amt(amount_str)
                if amount > 10: all_amounts.append(amount)
            except: continue
            
    end_text_segment = text[-int(len(text)*0.3):]
    numbers = re.findall(r'[\d\s,]+\s*\.\s*\d{2}', end_text_segment)
    if numbers:
        for n in numbers:
            try:
                amt = clean_amt(n)
                if amt > 10: all_amounts.append(amt)
            except: pass
            
    if not all_amounts:
        numbers = re.findall(r'[\d,]+\.\d{2}', text)
        if numbers:
            for n in numbers:
                try:
                    amt = clean_amt(n)
                    if amt > 10: all_amounts.append(amt)
                except: pass
                
    fallback_pattern = r'(?:TOTAL|GRAND\s+TOTAL)\s+[^\d]*(\d+)\s+(\d{2})\b'
    match = re.search(fallback_pattern, text, re.IGNORECASE)
    if match:
        all_amounts.append(float(f"{match.group(1)}.{match.group(2)}"))
        
    emergency_pattern = r'(?:TOTAL|GRANDTOTAL).*?([\d,]{2,})[\.\sX]*(\d{2})'
    match = re.search(emergency_pattern, text, re.IGNORECASE)
    if match:
         amt = float(f"{match.group(1).replace(',','')}.{match.group(2)}")
         if amt > 10: all_amounts.append(amt)
        
    if all_amounts: return max(all_amounts)
    return None

if len(sys.argv) < 2:
    print("Usage: python test_image.py <image_path>")
    sys.exit(1)

raw_text = sys.argv[1]

# Instead of passing a file, we can pass the raw string from the user's OCR output to test instantly
print(f"\n--- Processing RAW TEXT ---")
print(raw_text)
print("-" * 20)

gstin = extract_gstin(raw_text)
date = extract_invoice_date(raw_text)
amount = extract_total_amount(raw_text)

print(f"\nExtracted GSTIN: {gstin}")
print(f"Extracted Date : {date}")
print(f"Extracted Amt  : {amount}")
