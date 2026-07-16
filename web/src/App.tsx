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
import './styles/magic-animations.css';
import './styles/nav.css';

const GITHUB_URL = 'https://github.com/jingyu-wang/lite-agent-harness';

const GitHubRedirect: React.FC = () => {
  React.useEffect(() => {
    window.location.href = GITHUB_URL;
  }, []);
  return null;
};

const App: React.FC = () => {
  const location = useLocation();

  return (
    <>
      <ParticleCanvas />
      <NavBar />
      <main style={{ paddingTop: 56, minHeight: '100vh' }}>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/guide" element={<GuidePage />} />
            <Route path="/learn" element={<LearnPage />} />
            <Route path="/agent" element={<AgentPage />} />
            <Route path="/github" element={<GitHubRedirect />} />
          </Routes>
        </AnimatePresence>
      </main>
    </>
  );
};

export default App;
