import { useEffect, useState } from 'react';
import './App.css'; // We will use this for custom styles

function App() {
  const [user, setUser] = useState(null);
  // This object is made available by the script we added in index.html
  const webApp = window.Telegram.WebApp;

  useEffect(() => {
    // This function is called when the component is first loaded
    if (webApp) {
      webApp.ready(); // Let Telegram know the web app is ready

      // Set the user state from the data sent by Telegram
      if (webApp.initDataUnsafe?.user) {
        setUser(webApp.initDataUnsafe.user);
      }
      
      // Expand the app to full screen
      webApp.expand();

      // Optional: Change the background color to match the Telegram theme
      if (webApp.themeParams.bg_color) {
        document.body.style.backgroundColor = webApp.themeParams.bg_color;
      }
    }
  }, []); // The empty array means this effect runs only once

  // A simple loading state
  if (!user) {
    return (
      <div className="app-container">
        <h1>Loading...</h1>
      </div>
    );
  }

  // The main view after user data is loaded
  return (
    <div className="app-container">
      <div className="header">
        <h1>Dashboard</h1>
        <p className="welcome-message">
          Salom, <strong>{user.first_name}!</strong>
        </p>
      </div>
      
      <div className="user-info">
        <h3>Your Telegram Info:</h3>
        <p><strong>ID:</strong> <code>{user.id}</code></p>
        <p><strong>Username:</strong> @{user.username || 'not available'}</p>
        <p><strong>Language:</strong> {user.language_code}</p>
      </div>

      <div className="hint">
        <p>Bu bizning kelajakdagi Dashboardimizning boshlang'ich nuqtasi.</p>
        <p>Keyingi qadamda bu yerga "Yangi Post Yaratish" bo'limini qo'shamiz.</p>
      </div>
    </div>
  );
}

export default App
