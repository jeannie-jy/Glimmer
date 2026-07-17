import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import NavBar from './components/NavBar';
import ParticleCanvas from './components/ParticleCanvas';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import GuidePage from './pages/GuidePage';
import LearnPage from './pages/LearnPage';
import AgentPage from './pages/AgentPage';
import LoginPage from './pages/LoginPage';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import './styles/magic-animations.css';
import './styles/nav.css';

const GITHUB_URL = 'https://github.com/jeannie-jy/Glimmer';

const GitHubRedirect: React.FC = () => {
  React.useEffect(() => {
    window.location.href = GITHUB_URL;
  }, []);
  return null;
};

const App: React.FC = () => {
  const location = useLocation();

  return (
    <AuthProvider>
      <ParticleCanvas />
      <NavBar />
      <main style={{ paddingTop: 56, minHeight: '100vh' }}>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/guide" element={<GuidePage />} />
            <Route path="/learn" element={<LearnPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/agent" element={<ProtectedRoute><AgentPage /></ProtectedRoute>} />
            <Route path="/github" element={<GitHubRedirect />} />
          </Routes>
        </AnimatePresence>
      </main>
    </AuthProvider>
  );
};

export default App;
