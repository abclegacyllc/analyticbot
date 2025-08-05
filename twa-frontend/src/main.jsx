import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { AppProvider } from './context/AppContext'; // Yaratgan provayderimizni import qilamiz

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppProvider> {/* Butun ilovani provayder bilan o'raymiz */}
      <App />
    </AppProvider>
  </React.StrictMode>,
)
