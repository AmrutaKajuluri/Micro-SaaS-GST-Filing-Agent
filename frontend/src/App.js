import React, { useState } from 'react';
import InvoiceUpload from './components/InvoiceUpload';
import GSTResults from './components/GSTResults';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';

function App() {
  const [invoiceData, setInvoiceData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInvoiceProcessed = (data) => {
    setInvoiceData(data);
    setIsLoading(false);
    setError(null);
  };

  const handleLoading = (loading) => {
    setIsLoading(loading);
  };

  const handleError = (errorMessage) => {
    setError(errorMessage);
    setIsLoading(false);
  };

  const handleReset = () => {
    setInvoiceData(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              <p className="mt-4 text-gray-600">Processing your invoice...</p>
            </div>
          )}

          {/* Main Content */}
          {!isLoading && !invoiceData && (
            <div>
              <InvoiceUpload
                onInvoiceProcessed={handleInvoiceProcessed}
                onLoading={handleLoading}
                onError={handleError}
              />
            </div>
          )}

          {/* Results Display */}
          {!isLoading && invoiceData && (
            <GSTResults
              data={invoiceData}
              onReset={handleReset}
            />
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default App;
