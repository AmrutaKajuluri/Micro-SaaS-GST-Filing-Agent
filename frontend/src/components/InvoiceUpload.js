import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileImage, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

const InvoiceUpload = ({ onInvoiceProcessed, onLoading, onError }) => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setUploadedFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png']
    },
    maxFiles: 1,
    multiple: false
  });

  const handleProcess = async () => {
    if (!uploadedFile) return;

    onLoading(true);
    onError(null);

    const formData = new FormData();
    formData.append('file', uploadedFile);

    try {
      const response = await axios.post('/api/process-invoice', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        onInvoiceProcessed(response.data);
      } else {
        onError(response.data.error || 'Processing failed');
      }
    } catch (error) {
      console.error('Error processing invoice:', error);
      onError(error.response?.data?.error || 'Failed to process invoice. Please try again.');
    }
  };

  const handleReset = () => {
    setUploadedFile(null);
    setPreview(null);
    onError(null);
  };

  return (
    <div className="space-y-8">
      {/* Upload Section */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Upload Invoice</h2>
        <p className="text-gray-600 mb-8">
          Upload a clear image of your GST invoice to extract information automatically
        </p>
      </div>

      {!uploadedFile ? (
        <div className="max-w-2xl mx-auto">
          <div
            {...getRootProps()}
            className={`upload-area p-12 text-center cursor-pointer rounded-xl transition-all ${
              isDragActive ? 'dragover' : 'hover:border-primary-400 hover:bg-primary-50'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            {isDragActive ? (
              <div>
                <p className="text-xl font-semibold text-primary-600 mb-2">
                  Drop your invoice here
                </p>
                <p className="text-gray-600">Release to upload</p>
              </div>
            ) : (
              <div>
                <p className="text-xl font-semibold text-gray-700 mb-2">
                  Drag & drop your invoice here
                </p>
                <p className="text-gray-600 mb-4">or</p>
                <button className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                  Browse Files
                </button>
                <p className="text-sm text-gray-500 mt-4">
                  Supported formats: JPG, JPEG, PNG
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <FileImage className="w-6 h-6 text-green-600" />
                <div>
                  <p className="font-semibold text-gray-800">{uploadedFile.name}</p>
                  <p className="text-sm text-gray-600">
                    {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={handleReset}
                className="text-red-600 hover:text-red-800 transition-colors"
              >
                Remove
              </button>
            </div>

            {preview && (
              <div className="mb-6">
                <img
                  src={preview}
                  alt="Invoice preview"
                  className="w-full h-64 object-contain bg-gray-50 rounded-lg"
                />
              </div>
            )}

            <div className="flex justify-center space-x-4">
              <button
                onClick={handleProcess}
                className="px-8 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center space-x-2"
              >
                <CheckCircle className="w-5 h-5" />
                <span>Extract GST Information</span>
              </button>
              <button
                onClick={handleReset}
                className="px-8 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Upload Different File
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="max-w-4xl mx-auto mt-12">
        <h3 className="text-xl font-semibold text-gray-800 mb-6 text-center">
          How It Works
        </h3>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-primary-600 font-bold">1</span>
            </div>
            <h4 className="font-semibold text-gray-800 mb-2">Upload Invoice</h4>
            <p className="text-sm text-gray-600">
              Upload a clear image of your GST invoice in JPG or PNG format
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-primary-600 font-bold">2</span>
            </div>
            <h4 className="font-semibold text-gray-800 mb-2">AI Processing</h4>
            <p className="text-sm text-gray-600">
              Our AI extracts GSTIN, invoice date, amount, and calculates GST
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-primary-600 font-bold">3</span>
            </div>
            <h4 className="font-semibold text-gray-800 mb-2">Download CSV</h4>
            <p className="text-sm text-gray-600">
              Review extracted data and download GSTR-1 ready CSV file
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvoiceUpload;
