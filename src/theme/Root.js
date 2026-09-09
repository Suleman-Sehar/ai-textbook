import React from 'react';
import ErrorBoundary from '@site/src/components/ErrorBoundary';
import { setupGlobalErrorHandler } from '@site/src/utils/errorHandling';
import BrowserOnly from '@docusaurus/BrowserOnly';

// Initialize global error handler when the app loads
setupGlobalErrorHandler();

const Root = ({ children }) => {
  return (
    <ErrorBoundary>
      {children}
      <BrowserOnly fallback={null}>
        {() => {
          const ChatbotWidget = require('@site/src/components/ChatbotWidget').default;
          return <ChatbotWidget />;
        }}
      </BrowserOnly>
    </ErrorBoundary>
  );
};

export default Root;