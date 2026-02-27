import re
from typing import Dict, Tuple, Optional

class GSTLogic:
    """
    Handles GST validation, tax calculation, and GSTR-1 formatting.
    """
    
    def __init__(self):
        # Indian state codes mapped to state names
        self.state_codes = {
            '37': 'Andhra Pradesh',
            '10': 'Maharashtra',
            '05': 'Uttar Pradesh',
            '06': 'Uttarakhand',
            '07': 'Bihar',
            '08': 'West Bengal',
            '09': 'Uttar Pradesh',
            '11': 'Sikkim',
            '12': 'Kerala',
            '13': 'Delhi',
            '14': 'Rajasthan',
            '15': 'Haryana',
            '16': 'Punjab',
            '17': 'Himachal Pradesh',
            '18': 'Jammu & Kashmir',
            '19': 'Karnataka',
            '20': 'Gujarat',
            '21': 'Madhya Pradesh',
            '22': 'Chhattisgarh',
            '23': 'Tamil Nadu',
            '24': 'Telangana',
            '25': 'Andhra Pradesh',
            '26': 'Goa',
            '27': 'Gujarat',
            '28': 'Karnataka',
            '29': 'Madhya Pradesh',
            '30': 'Maharashtra',
            '31': 'Odisha',
            '32': 'Telangana',
            '33': 'Sikkim',
            '34': 'Tripura',
            '35': 'West Bengal',
            '36': 'Lakshadweep',
            '38': 'Karnataka',
            '39': 'Goa',
            '40': 'Daman and Diu',
            '41': 'Daman and Diu',
            '42': 'Daman and Diu',
            '43': 'Daman and Diu',
            '46': 'Ladakh',
            '47': 'Dadra and Nagar Haveli and Daman and Diu',
            '48': 'Dadra and Nagar Haveli and Daman and Diu',
            '49': 'Tamil Nadu',
            '50': 'Tamil Nadu'
        }
    
    def validate_gstin(self, gstin: str) -> bool:
        """
        Validate GSTIN format using regex.
        GSTIN format: 2 digits (state code) + 10 characters (PAN) + 1 digit + 1 character + 1 character (Z)
        """
        if not gstin or len(gstin) != 15:
            return False
        
        # GSTIN regex pattern
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1}$'
        return bool(re.match(pattern, gstin.upper()))
    
    def get_state_from_gstin(self, gstin: str) -> Optional[str]:
        """
        Extract state name from GSTIN using first 2 digits (state code).
        """
        if not gstin or len(gstin) < 2:
            return None
        
        state_code = gstin[:2]
        return self.state_codes.get(state_code, f'Unknown State ({state_code})')
    
    def calculate_gst_split(self, total_amount: float, gstin: str) -> Dict[str, float]:
        """
        Calculate GST split based on state code in GSTIN.
        
        For intra-state sales (same state):
        - CGST: 9% of taxable value
        - SGST: 9% of taxable value
        - Total GST: 18%
        
        For inter-state sales:
        - IGST: 18% of taxable value
        
        Special case: If state code is 37 (Andhra Pradesh), apply CGST+SGST split
        """
        if not total_amount or total_amount <= 0:
            return {'cgst': 0.0, 'sgst': 0.0, 'igst': 0.0, 'total_gst': 0.0}
        
        # Assume 18% GST rate (standard rate for most goods)
        gst_rate = 0.18
        
        # Calculate taxable value (amount before GST)
        # For simplicity, assuming total amount includes GST
        taxable_value = total_amount / (1 + gst_rate)
        total_gst = total_amount - taxable_value
        
        # Check if it's intra-state (same state) or inter-state
        # For this demo, we'll use the state code from GSTIN
        state_code = gstin[:2] if gstin else "00"
        
        # Special case: Andhra Pradesh (37) - apply CGST+SGST split
        # In real implementation, this would depend on seller's state
        if state_code == '37':
            # Intra-state sale: CGST + SGST
            cgst = total_gst / 2
            sgst = total_gst / 2
            igst = 0.0
        else:
            # Default to inter-state: IGST
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
    
    def format_gstr1_row(self, invoice_data: Dict[str, any]) -> Dict[str, str]:
        """
        Format invoice data into GSTR-1 CSV format.
        
        GSTR-1 B2B invoices require these columns:
        - GSTIN/UIN of Recipient
        - Invoice Date
        - Invoice Value
        - Place of Supply (State code)
        - Reverse Charge (Y/N)
        - Invoice Type (Regular/SEZ/Deemed Export)
        """
        gstin = invoice_data.get('gstin', '')
        invoice_date = invoice_data.get('invoice_date', '')
        total_amount = invoice_data.get('total_amount', 0.0)
        
        # Get place of supply from GSTIN
        place_of_supply = self.get_state_from_gstin(gstin) if gstin else 'Unknown'
        state_code = gstin[:2] if gstin else '00'
        
        # Format invoice value
        invoice_value = f"{total_amount:.2f}" if total_amount else "0.00"
        
        # Reverse charge: N for most cases (Y only for specific services)
        reverse_charge = 'N'
        
        # Invoice type: Regular for most cases
        invoice_type = 'Regular'
        
        return {
            'GSTIN/UIN of Recipient': gstin or '',
            'Invoice Date': invoice_date or '',
            'Invoice Value': invoice_value,
            'Place of Supply': f"{place_of_supply} ({state_code})",
            'Reverse Charge': reverse_charge,
            'Invoice Type': invoice_type
        }
    
    def process_invoice(self, invoice_data: Dict[str, any]) -> Dict[str, any]:
        """
        Process complete invoice with GST calculations and GSTR-1 formatting.
        """
        gstin = invoice_data.get('gstin', '')
        total_amount = invoice_data.get('total_amount', 0.0)
        
        # Validate GSTIN
        is_valid_gstin = self.validate_gstin(gstin) if gstin else False
        
        # Calculate GST split
        gst_calculation = self.calculate_gst_split(total_amount, gstin)
        
        # Format for GSTR-1
        gstr1_row = self.format_gstr1_row(invoice_data)
        
        return {
            'original_data': invoice_data,
            'is_valid_gstin': is_valid_gstin,
            'state': self.get_state_from_gstin(gstin) if gstin else None,
            'gst_calculation': gst_calculation,
            'gstr1_row': gstr1_row
        }
