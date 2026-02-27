import streamlit as st
import pandas as pd
import io
from PIL import Image
import tempfile
import os
from utils.extractor import InvoiceExtractor
from utils.gst_logic import GSTLogic

# Set page configuration
st.set_page_config(
    page_title="AI GST Filing Agent for Kirana Stores",
    page_icon="🧾",
    layout="wide"
)

# Initialize classes
@st.cache_resource
def load_extractor():
    return InvoiceExtractor()

@st.cache_resource
def load_gst_logic():
    return GSTLogic()

# Main application
def main():
    # Title and description
    st.title("🧾 AI GST Filing Agent for Kirana Stores")
    st.markdown("""
    **Automated GST Invoice Processing for Small Businesses**
    
    Upload your invoice images and automatically extract GST details to generate GSTR-1 filings.
    """)
    
    # Initialize classes
    extractor = load_extractor()
    gst_logic = load_gst_logic()
    
    # File upload section
    st.header("📤 Upload Invoice")
    
    # Create file uploader
    uploaded_file = st.file_uploader(
        "Choose an invoice image (JPG/PNG)",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear image of your GST invoice"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Uploaded Invoice")
            image = Image.open(uploaded_file)
            st.image(image, caption="Invoice Image", use_column_width=True)
        
        # Process button
        if st.button("🔍 Extract GST Information", type="primary"):
            with st.spinner("Processing invoice..."):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Extract information
                    invoice_info = extractor.extract_invoice_info(tmp_file_path)
                    
                    # Process with GST logic
                    processed_data = gst_logic.process_invoice(invoice_info)
                    
                    # Display results
                    with col2:
                        st.subheader("📊 Extracted Information")
                        
                        # GSTIN
                        gstin = invoice_info.get('gstin', 'Not Found')
                        gstin_status = "✅ Valid" if processed_data['is_valid_gstin'] else "❌ Invalid/Not Found"
                        st.write(f"**GSTIN:** {gstin} {gstin_status}")
                        
                        # Invoice Date
                        invoice_date = invoice_info.get('invoice_date', 'Not Found')
                        st.write(f"**Invoice Date:** {invoice_date}")
                        
                        # Total Amount
                        total_amount = invoice_info.get('total_amount', 0)
                        st.write(f"**Total Amount:** ₹{total_amount:.2f}" if total_amount else "**Total Amount:** Not Found")
                        
                        # State
                        state = processed_data['state']
                        st.write(f"**State:** {state}" if state else "**State:** Not Determined")
                    
                    # GST Calculation Details
                    st.subheader("💰 GST Calculation Details")
                    gst_calc = processed_data['gst_calculation']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Taxable Value", f"₹{gst_calc['taxable_value']:.2f}")
                    with col2:
                        st.metric("CGST", f"₹{gst_calc['cgst']:.2f}")
                    with col3:
                        st.metric("SGST", f"₹{gst_calc['sgst']:.2f}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("IGST", f"₹{gst_calc['igst']:.2f}")
                    with col2:
                        st.metric("Total GST", f"₹{gst_calc['total_gst']:.2f}")
                    
                    # GST Logic Explanation
                    with st.expander("📚 GST Logic Explanation"):
                        st.markdown("""
                        **GST Tax Structure Applied:**
                        
                        - **Standard Rate:** 18% (applicable to most goods)
                        - **Intra-state (Andhra Pradesh - 37):** CGST 9% + SGST 9%
                        - **Inter-state (Other states):** IGST 18%
                        
                        **Calculation Formula:**
                        - Taxable Value = Invoice Amount ÷ (1 + GST Rate)
                        - GST Amount = Invoice Amount - Taxable Value
                        
                        **Note:** This is a simplified calculation. Actual GST rates may vary 
                        based on product categories and applicable tax laws.
                        """)
                    
                    # GSTR-1 Preview
                    st.subheader("📋 GSTR-1 Preview")
                    gstr1_data = processed_data['gstr1_row']
                    
                    # Create DataFrame for display
                    df = pd.DataFrame([gstr1_data])
                    st.dataframe(df, use_container_width=True)
                    
                    # CSV Download
                    st.subheader("💾 Download GSTR-1 CSV")
                    
                    # Create CSV
                    csv = df.to_csv(index=False)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download GSTR-1 CSV",
                        data=csv,
                        file_name=f"GSTR-1_{gstin if gstin else 'invoice'}_{invoice_date if invoice_date else 'date'}.csv",
                        mime="text/csv",
                        type="primary"
                    )
                    
                    # Raw extracted text (for debugging)
                    with st.expander("🔍 Raw Extracted Text"):
                        st.text_area("Extracted Text", invoice_info.get('extracted_text', ''), height=200)
                
                except Exception as e:
                    st.error(f"Error processing invoice: {str(e)}")
                    st.info("Please ensure the invoice image is clear and contains readable GST information.")
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
    
    # Instructions section
    st.header("📖 How to Use")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Step 1: Upload Invoice**
        - Click 'Browse files'
        - Select JPG/PNG invoice image
        - Ensure image is clear and readable
        """)
    
    with col2:
        st.markdown("""
        **Step 2: Extract Information**
        - Click 'Extract GST Information'
        - AI will process the image
        - Review extracted details
        """)
    
    with col3:
        st.markdown("""
        **Step 3: Download CSV**
        - Review GSTR-1 preview
        - Click 'Download GSTR-1 CSV'
        - Use file for GST filing
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🤖 AI GST Filing Agent | Built for Kirana Stores | Simplifying GST Compliance</p>
        <p><small>Note: This tool assists with GST filing. Always verify extracted information before submission.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
