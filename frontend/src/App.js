import React, { useState, useEffect } from 'react';
import { Cloudinary } from '@cloudinary/url-gen';
import { AdvancedImage } from '@cloudinary/react';
import { fill } from '@cloudinary/url-gen/actions/resize';
import './App.css';

// Initialize Cloudinary
// (Replace 'demo' with your CLOUDINARY_CLOUD_NAME from .env once you have it)
const cld = new Cloudinary({
  cloud: {
    cloudName: 'demo' 
  }
});

function App() {
  const [authState, setAuthState] = useState({
    isLoading: true,
    isAuthenticated: false,
    user: null,
    error: null
  });

  useEffect(() => {
    // Check initial auth state by asking the Flask backend
    fetch('/api/auth/profile')
      .then(res => {
        if (!res.ok) {
          throw new Error('Not authenticated');
        }
        return res.json();
      })
      .then(data => {
        setAuthState({
          isLoading: false,
          isAuthenticated: true,
          user: data.user,
          error: null
        });
      })
      .catch(err => {
        setAuthState({
          isLoading: false,
          isAuthenticated: false,
          user: null,
          error: err.message
        });
      });
  }, []);

  const handleLogin = () => {
    // Redirect browser directly to Flask's login route on port 5000
    window.location.href = 'http://127.0.0.1:5000/login';
  };

  const handleLogout = () => {
    // Ask Flask for the Auth0 logout URL, then redirect browser there
    fetch('http://127.0.0.1:5000/api/auth/logout')
      .then(res => res.json())
      .then(data => {
        if (data.logout_url) {
          window.location.href = data.logout_url;
        }
      });
  };

  // Example Cloudinary image transformations
  const myImage = cld.image('cld-sample-2'); 
  myImage.resize(fill().width(400).height(250));

  return (
    <div className="App">
      <header className="app-header">
        <h1 className="app-title">React + Flask Auth0</h1>
        <h2 className="app-subtitle">Powered by Cloudinary</h2>
      </header>

      <main className="auth-card">
        {authState.isLoading ? (
          <div>Loading your profile...</div>
        ) : authState.isAuthenticated ? (
          <div className="profile-section">
            <div className="profile-info">
              <h3>Welcome, {authState.user?.name || authState.user?.email || 'User'}!</h3>
              <p>You have successfully logged in via Auth0.</p>
            </div>
            
            <button className="auth-button" onClick={handleLogout}>
              Logout
            </button>

            <div className="cloudinary-demo">
              <h4>Here's a sample image dynamically rendered and styled by Cloudinary's React SDK:</h4>
              <AdvancedImage className="demo-image" cldImg={myImage} />
            </div>
          </div>
        ) : (
          <div className="profile-section">
            <div className="profile-info">
              <h3>Welcome Guest</h3>
              <p>Please log in to continue.</p>
            </div>
            <button className="auth-button" onClick={handleLogin}>
              Log In securely with Auth0
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
