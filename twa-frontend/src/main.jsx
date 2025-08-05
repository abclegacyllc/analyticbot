import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// AppProvider endi kerak emas, chunki Zustand global holatni o'zi boshqaradi.
// React.StrictMode'ni ham olib tashladik, chunki u TWA bilan muammo keltirib chiqarayotgan edi.
ReactDOM.createRoot(document.getElementById('root')).render(
  <App />
)
