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
    st.header("📤 Upload Invoices")
    
    # Create file uploader
    uploaded_files = st.file_uploader(
        "Choose invoice images (JPG/PNG). You can select multiple files.",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Upload clear images of your GST invoices"
    )
    
    if uploaded_files:
        st.write(f"📚 {len(uploaded_files)} file(s) uploaded.")
        
        # Process button
        if st.button("🔍 Process All Invoices", type="primary"):
            
            all_gstr1_data = [] # To store rows for the combined CSV
            
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing invoice {i+1} of {len(uploaded_files)}: {uploaded_file.name}")
                
                # Display uploaded image and results in a container
                with st.expander(f"📄 Invoice: {uploaded_file.name}", expanded=(len(uploaded_files)==1)):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        image = Image.open(uploaded_file)
                        st.image(image, caption=uploaded_file.name, use_column_width=True)
                        
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Extract information
                        invoice_info = extractor.extract_invoice_info(tmp_file_path)
                        
                        # Process with GST logic
                        processed_data = gst_logic.process_invoice(invoice_info)
                        
                        # Append the row to our bulk data collection
                        all_gstr1_data.append(processed_data['gstr1_row'])
                        
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
                        
                        calc_col1, calc_col2, calc_col3 = st.columns(3)
                        with calc_col1:
                            st.metric("Taxable Value", f"₹{gst_calc['taxable_value']:.2f}")
                        with calc_col2:
                            st.metric("CGST", f"₹{gst_calc['cgst']:.2f}")
                        with calc_col3:
                            st.metric("SGST", f"₹{gst_calc['sgst']:.2f}")
                        
                        calc_col1, calc_col2 = st.columns(2)
                        with calc_col1:
                            st.metric("IGST", f"₹{gst_calc['igst']:.2f}")
                        with calc_col2:
                            st.metric("Total GST", f"₹{gst_calc['total_gst']:.2f}")
                        
                        # Raw extracted text (for debugging)
                        with st.expander("🔍 Raw Extracted Text"):
                            st.text_area("Extracted Text", invoice_info.get('extracted_text', ''), height=200, key=f"raw_{i}")
                    
                    except Exception as e:
                        st.error(f"Error processing invoice: {str(e)}")
                        st.info("Please ensure the invoice image is clear and contains readable GST information.")
                    
                    finally:
                        # Clean up temporary file
                        if os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
                            
                # Update progress bar
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_text.text(f"✅ Successfully processed {len(all_gstr1_data)} invoices.")
            
            # --- OVERALL BULK EXPORT SECTION ---
            if all_gstr1_data:
                st.markdown("---")
                st.header("📋 Consolidated GSTR-1 Preview")
                
                # Create DataFrame for display
                bulk_df = pd.DataFrame(all_gstr1_data)
                st.dataframe(bulk_df, use_container_width=True)
                
                # CSV Download
                st.subheader("💾 Download Consolidated CSV")
                
                # Create CSV
                bulk_csv = bulk_df.to_csv(index=False)
                
                # Download button
                st.download_button(
                    label=f"📥 Download Bulk GSTR-1 ({len(all_gstr1_data)} Invoices)",
                    data=bulk_csv,
                    file_name="Bulk_GSTR-1_Filing.csv",
                    mime="text/csv",
                    type="primary"
                )
    
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
