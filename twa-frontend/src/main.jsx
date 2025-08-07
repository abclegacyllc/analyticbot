import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme.js';
import * as Sentry from "@sentry/react";

// Sentry'ni to'g'rilangan sozlamalar bilan ishga tushiramiz
Sentry.init({
  dsn: "https://1c970d384ec6c7f7f6ec0d9930801d250a4509801364324352.ingest.us.sentry.io/4509801366290432",
  integrations: [
    // Xato qator olib tashlandi
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  // Performance Monitoring
  tracesSampleRate: 1.0, 
  // Session Replay
  replaysSessionSampleRate: 0.1, 
  replaysOnErrorSampleRate: 1.0, 
});


ReactDOM.createRoot(document.getElementById('root')).render(
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <App />
  </ThemeProvider>
)
