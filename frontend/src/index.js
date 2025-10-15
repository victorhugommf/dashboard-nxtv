import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import ThemeProvider from './contexts/ThemeContext';
import ThemeErrorBoundary from './components/ThemeErrorBoundary';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeErrorBoundary>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </ThemeErrorBoundary>
  </React.StrictMode>
);

