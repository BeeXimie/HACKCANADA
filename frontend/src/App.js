import React, { useState, useEffect } from 'react';
import { Cloudinary } from '@cloudinary/url-gen';
import { AdvancedImage } from '@cloudinary/react';
import { fill } from '@cloudinary/url-gen/actions/resize';
import './App.css';

// Initialize Cloudinary
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

  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    fetch('/api/user/profile')
      .then(res => {
        if (!res.ok) throw new Error('Not authenticated');
        return res.json();
      })
      .then(data => {
        setAuthState({ isLoading: false, isAuthenticated: true, user: data.user, error: null });
      })
      .catch(err => {
        setAuthState({ isLoading: false, isAuthenticated: false, user: null, error: err.message });
      });
  }, []);

  const handleLogin = () => {
    window.location.href = '/login';
  };

  const handleLogout = () => {
    fetch('/logout')
      .then(res => res.json())
      .then(data => {
        if (data.logout_url) window.location.href = data.logout_url;
      });
  };

  const handleDeleteAccount = async () => {
    try {
      const response = await fetch('/api/user/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      if (data.logout_url) {
        window.location.href = data.logout_url;
      }
    } catch (err) {
      console.error("Delete failed", err);
      alert("Delete failed. Please try again.");
    }
  };

  const myImage = cld.image('cld-sample-2');
  myImage.resize(fill().width(400).height(250));

  return (
    <div className="App">
      {/* Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Delete Account?</h3>
            <p>Are you sure? This action is permanent and will delete all your profile data, applications, and essays.</p>
            <div className="modal-actions">
              <button className="cancel-btn" onClick={() => setShowDeleteModal(false)}>Cancel</button>
              <button className="confirm-delete-btn" onClick={handleDeleteAccount}>Yes, Delete My Account</button>
            </div>
          </div>
        </div>
      )}

      {/* Pill badge */}
      <div className="app-badge">
        ScholarSync <span className="app-badge-arrow">›</span>
      </div>

      {/* Hero heading */}
      <header className="app-header">
        <h1 className="app-title">
          Find the best scholarships<br />
          <span className="app-title-accent">matched to you</span>
        </h1>
      </header>

      <p className="app-subtitle">
        ScholarSync matches you with scholarships and helps you draft application essays.
      </p>

      {/* Auth card */}
      <main className="auth-card">
        {authState.isLoading ? (
          <div className="loading-state">Loading…</div>
        ) : authState.isAuthenticated ? (
          <div className="profile-section">
            <div className="profile-info">
              <h3>Welcome, {authState.user?.name || authState.user?.email || 'User'}!</h3>
              <p>You're logged in via Auth0.</p>
            </div>

            <button className="auth-button logout-btn" onClick={handleLogout}>
              Log Out
            </button>

            <button className="auth-button delete-btn" onClick={() => setShowDeleteModal(true)}>
              Delete Account
            </button>

            <div className="cloudinary-demo">
              <h4>Sample image via Cloudinary React SDK</h4>
              <AdvancedImage className="demo-image" cldImg={myImage} />
            </div>
          </div>
        ) : (
          <button className="auth-button" onClick={handleLogin}>
            Log in Securely with Auth0
          </button>
        )}
      </main>

    </div>
  );
}

export default App;