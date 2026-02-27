import React from 'react';
import { Bot, Heart } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white mt-16">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Bot className="w-5 h-5" />
            <span className="font-semibold">AI GST Filing Agent</span>
          </div>
          <p className="text-gray-300 mb-2">
            Built for Kirana Stores | Simplifying GST Compliance
          </p>
          <p className="text-sm text-gray-400 flex items-center justify-center">
            Made with <Heart className="w-4 h-4 mx-1 text-red-500" fill="currentColor" /> 
            for small businesses in India
          </p>
          <p className="text-xs text-gray-500 mt-3">
            Note: This tool assists with GST filing. Always verify extracted information before submission.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
