import re
from typing import Dict, Optional


class GSTLogic:
    """
    Handles GST validation, tax calculation, and GSTR-1 formatting.
    """

    def __init__(self):
        # Official Indian GST State Codes (Correct Mapping)
        self.state_codes = {
            '01': 'Jammu & Kashmir',
            '02': 'Himachal Pradesh',
            '03': 'Punjab',
            '04': 'Chandigarh',
            '05': 'Uttarakhand',
            '06': 'Haryana',
            '07': 'Delhi',
            '08': 'Rajasthan',
            '09': 'Uttar Pradesh',
            '10': 'Bihar',
            '11': 'Sikkim',
            '12': 'Arunachal Pradesh',
            '13': 'Nagaland',
            '14': 'Manipur',
            '15': 'Mizoram',
            '16': 'Tripura',
            '17': 'Meghalaya',
            '18': 'Assam',
            '19': 'West Bengal',
            '20': 'Jharkhand',
            '21': 'Odisha',
            '22': 'Chhattisgarh',
            '23': 'Madhya Pradesh',
            '24': 'Gujarat',
            '26': 'Dadra and Nagar Haveli and Daman and Diu',
            '27': 'Maharashtra',
            '28': 'Andhra Pradesh',
            '29': 'Karnataka',
            '30': 'Goa',
            '31': 'Lakshadweep',
            '32': 'Kerala',
            '33': 'Tamil Nadu',
            '34': 'Puducherry',
            '35': 'Andaman and Nicobar Islands',
            '36': 'Telangana',
            '37': 'Andhra Pradesh',
            '38': 'Ladakh'
        }

        # 👇 Assume seller is Andhra Pradesh (37) for demo
        self.seller_state_code = "37"

    # ---------------- GSTIN VALIDATION ----------------
    def validate_gstin(self, gstin: str) -> bool:
        if not gstin or len(gstin) != 15:
            return False

        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$'
        return bool(re.match(pattern, gstin.upper()))

    # ---------------- GET STATE ----------------
    def get_state_from_gstin(self, gstin: str) -> Optional[str]:
        if not gstin or len(gstin) < 2:
            return None

        state_code = gstin[:2]
        return self.state_codes.get(state_code, f"Unknown ({state_code})")

    # ---------------- GST CALCULATION ----------------
    def calculate_gst_split(self, total_amount: float, gstin: str) -> Dict[str, float]:

        if not total_amount or total_amount <= 0:
            return {
                'taxable_value': 0.0,
                'cgst': 0.0,
                'sgst': 0.0,
                'igst': 0.0,
                'total_gst': 0.0
            }

        gst_rate = 0.18  # Standard 18%
        taxable_value = total_amount / (1 + gst_rate)
        total_gst = total_amount - taxable_value

        buyer_state_code = gstin[:2] if gstin else "00"

        # Intra-state vs Inter-state logic
        if buyer_state_code == self.seller_state_code:
            # CGST + SGST
            cgst = total_gst / 2
            sgst = total_gst / 2
            igst = 0.0
        else:
            # IGST
            cgst = 0.0
            sgst = 0.0
            igst = total_gst

        return {
            'taxable_value': round(taxable_value, 2),
            'cgst': round(cgst, 2),
            'sgst': round(sgst, 2),
            'igst': round(igst, 2),
            'total_gst': round(total_gst, 2)
        }

    # ---------------- GSTR-1 FORMAT ----------------
    def format_gstr1_row(self, invoice_data: Dict[str, any]) -> Dict[str, str]:

        gstin = invoice_data.get('gstin', '')
        invoice_date = invoice_data.get('invoice_date', '')
        total_amount = invoice_data.get('total_amount', 0.0)

        state_name = self.get_state_from_gstin(gstin) if gstin else "Unknown"
        state_code = gstin[:2] if gstin else "00"

        return {
            'GSTIN/UIN of Recipient': gstin or '',
            'Invoice Date': invoice_date or '',
            'Invoice Value': f"{total_amount:.2f}",
            'Place of Supply': f"{state_name} ({state_code})",
            'Reverse Charge': 'N',
            'Invoice Type': 'Regular'
        }

    # ---------------- FULL PROCESS ----------------
    def process_invoice(self, invoice_data: Dict[str, any]) -> Dict[str, any]:

        gstin = invoice_data.get('gstin', '')
        total_amount = invoice_data.get('total_amount', 0.0)

        is_valid = self.validate_gstin(gstin) if gstin else False

        gst_calc = self.calculate_gst_split(total_amount, gstin)

        gstr1_row = self.format_gstr1_row(invoice_data)

        return {
            'original_data': invoice_data,
            'is_valid_gstin': is_valid,
            'state': self.get_state_from_gstin(gstin) if gstin else None,
            'gst_calculation': gst_calc,
            'gstr1_row': gstr1_row
        }