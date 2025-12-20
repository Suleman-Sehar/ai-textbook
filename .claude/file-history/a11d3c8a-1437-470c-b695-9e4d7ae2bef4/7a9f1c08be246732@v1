import React from 'react';
import ErrorBoundary from '@site/src/components/ErrorBoundary';
import { setupGlobalErrorHandler } from '@site/src/utils/errorHandling';

// Initialize global error handler when the app loads
setupGlobalErrorHandler();

const Root = ({ children }) => {
  return <ErrorBoundary>{children}</ErrorBoundary>;
};

export default Root;