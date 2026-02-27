import React, { useState } from 'react';
import { Download, ArrowLeft, CheckCircle, AlertCircle, FileText, Calculator, Info } from 'lucide-react';
import axios from 'axios';

const GSTResults = ({ data, onReset }) => {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadCSV = async () => {
    setIsDownloading(true);
    try {
      const response = await axios.post('/api/download-csv', {
        gstr1_data: data.gstr1_data,
        gstin: data.invoice_info.gstin || 'invoice',
        invoice_date: data.invoice_info.invoice_date || 'date'
      }, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `GSTR-1_${data.invoice_info.gstin || 'invoice'}_${data.invoice_info.invoice_date || 'date'}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading CSV:', error);
      alert('Failed to download CSV. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const { invoice_info, processed_data, gstr1_data } = data;
  const gst_calc = processed_data.gst_calculation;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">GST Processing Results</h2>
        <button
          onClick={onReset}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Upload New Invoice</span>
        </button>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Extracted Information */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-2 mb-4">
            <FileText className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-800">Extracted Information</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center py-3 border-b">
              <span className="text-gray-600">GSTIN:</span>
              <div className="flex items-center space-x-2">
                <span className="font-medium">{invoice_info.gstin || 'Not Found'}</span>
                {processed_data.is_valid_gstin ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-600" />
                )}
              </div>
            </div>
            
            <div className="flex justify-between items-center py-3 border-b">
              <span className="text-gray-600">Invoice Date:</span>
              <span className="font-medium">{invoice_info.invoice_date || 'Not Found'}</span>
            </div>
            
            <div className="flex justify-between items-center py-3 border-b">
              <span className="text-gray-600">Total Amount:</span>
              <span className="font-medium">
                {invoice_info.total_amount ? `₹${invoice_info.total_amount.toFixed(2)}` : 'Not Found'}
              </span>
            </div>
            
            <div className="flex justify-between items-center py-3">
              <span className="text-gray-600">State:</span>
              <span className="font-medium">{processed_data.state || 'Not Determined'}</span>
            </div>
          </div>
        </div>

        {/* GST Calculation */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Calculator className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-800">GST Calculation</h3>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Taxable Value</p>
                <p className="text-xl font-bold text-blue-600">₹{gst_calc.taxable_value.toFixed(2)}</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Total GST</p>
                <p className="text-xl font-bold text-green-600">₹{gst_calc.total_gst.toFixed(2)}</p>
              </div>
            </div>
            
            <div className="space-y-2 pt-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">CGST (9%):</span>
                <span className="font-medium">₹{gst_calc.cgst.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">SGST (9%):</span>
                <span className="font-medium">₹{gst_calc.sgst.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="text-gray-600">IGST (18%):</span>
                <span className="font-medium">₹{gst_calc.igst.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* GSTR-1 Preview */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center space-x-2 mb-4">
          <FileText className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-800">GSTR-1 Preview</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-50">
                <th className="border border-gray-200 px-4 py-2 text-left text-sm font-medium text-gray-700">GSTIN/UIN of Recipient</th>
                <th className="border border-gray-200 px-4 py-2 text-left text-sm font-medium text-gray-700">Invoice Date</th>
                <th className="border border-gray-200 px-4 py-2 text-left text-sm font-medium text-gray-700">Invoice Value</th>
                <th className="border border-gray-200 px-4 py-2 text-left text-sm font-medium text-gray-700">Place of Supply</th>
                <th className="border border-gray-200 px-4 py-2 text-left text-sm font-medium text-gray-700">Reverse Charge</th>
                <th className="border border-gray-200 px-4 py-2 text-left text-sm font-medium text-gray-700">Invoice Type</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-gray-200 px-4 py-2 text-sm">{gstr1_data['GSTIN/UIN of Recipient']}</td>
                <td className="border border-gray-200 px-4 py-2 text-sm">{gstr1_data['Invoice Date']}</td>
                <td className="border border-gray-200 px-4 py-2 text-sm">{gstr1_data['Invoice Value']}</td>
                <td className="border border-gray-200 px-4 py-2 text-sm">{gstr1_data['Place of Supply']}</td>
                <td className="border border-gray-200 px-4 py-2 text-sm">{gstr1_data['Reverse Charge']}</td>
                <td className="border border-gray-200 px-4 py-2 text-sm">{gstr1_data['Invoice Type']}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* GST Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start space-x-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-900 mb-2">GST Logic Applied</h4>
            <div className="text-sm text-blue-800 space-y-1">
              <p><strong>Standard Rate:</strong> 18% (applicable to most goods)</p>
              <p><strong>Intra-state (Andhra Pradesh - 37):</strong> CGST 9% + SGST 9%</p>
              <p><strong>Inter-state (Other states):</strong> IGST 18%</p>
              <p className="mt-2"><strong>Calculation:</strong> Taxable Value = Invoice Amount ÷ (1 + GST Rate)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Download Section */}
      <div className="text-center">
        <button
          onClick={handleDownloadCSV}
          disabled={isDownloading}
          className="inline-flex items-center space-x-2 px-8 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className="w-5 h-5" />
          <span>{isDownloading ? 'Downloading...' : 'Download GSTR-1 CSV'}</span>
        </button>
        <p className="text-sm text-gray-600 mt-2">
          Download the GSTR-1 ready CSV file for your GST filing
        </p>
      </div>

      {/* Raw Text (Optional) */}
      {invoice_info.extracted_text && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-2 mb-4">
            <FileText className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-800">Raw Extracted Text</h3>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
              {invoice_info.extracted_text}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default GSTResults;
