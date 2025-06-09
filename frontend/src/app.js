
import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import Auth from './components/Auth/Auth';
import ChatLayout from './components/ChatLayout/ChatLayout';
import api from './services/api';
import jwtDecode from 'jwt-decode';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const handleLogout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setIsAuthenticated(false);
    setUser(null);
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decodedToken = jwtDecode(token);
        if (decodedToken.exp * 1000 > Date.now()) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          setUser({ username: decodedToken.sub });
          setIsAuthenticated(true);
        } else {
          handleLogout();
        }
      } catch (error) {
        console.error("Invalid token:", error);
        handleLogout();
      }
    }
    setIsLoading(false);
  }, []);

  const handleLogin = (token) => {
    localStorage.setItem('token', token);
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    const decodedToken = jwtDecode(token);
    setUser({ username: decodedToken.sub });
    setIsAuthenticated(true);
  };

  if (isLoading) {
    return <div style={{ textAlign: 'center', marginTop: '5rem' }}>Loading...</div>;
  }

  return (
    <div className="app-container">
      <Routes>
        <Route 
          path="/auth" 
          element={!isAuthenticated ? <Auth onLogin={handleLogin} /> : <Navigate to="/chat" />} 
        />
        <Route 
          path="/chat/*" 
          element={isAuthenticated ? <ChatLayout user={user} onLogout={handleLogout} /> : <Navigate to="/auth" />} 
        />
        <Route 
          path="/" 
          element={<Navigate to={isAuthenticated ? "/chat" : "/auth"} />} 
        />
      </Routes>
    </div>
  );
}

export default App;