import React from 'react';
import { FileText, Sparkles } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-white shadow-lg">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-center">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <FileText className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800 flex items-center">
                AI GST Filing Agent
                <Sparkles className="w-6 h-6 ml-2 text-yellow-500" />
              </h1>
              <p className="text-gray-600 mt-1">
                Automated GST Invoice Processing for Kirana Stores
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
