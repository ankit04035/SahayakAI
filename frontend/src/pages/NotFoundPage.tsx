import React from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowLeft, Home } from 'lucide-react';
import { Button } from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <div className="w-16 h-16 rounded-full bg-primary-50 text-primary-600 flex items-center justify-center mb-4">
        <AlertCircle className="w-8 h-8" />
      </div>
      <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl mb-2">404</h1>
      <h2 className="text-xl font-semibold text-gray-800 mb-3">Page Not Found</h2>
      <p className="text-gray-500 max-w-md mb-6 text-sm">
        The page you are looking for doesn't exist or has been moved. Use the navigation links or return to the main dashboard.
      </p>
      <Link to="/">
        <Button leftIcon={<Home className="w-4 h-4" />}>
          Back to Dashboard
        </Button>
      </Link>
    </div>
  );
};
