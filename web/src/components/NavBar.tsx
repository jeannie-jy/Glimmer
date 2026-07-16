import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import GitHubStarButton from './GitHubStarButton';

const NAV_ITEMS = [
  { path: '/', label: 'Home', icon: '🏠' },
  { path: '/about', label: 'About', icon: '📖' },
  { path: '/guide', label: 'Guide', icon: '🧭' },
  { path: '/learn', label: 'Learn', icon: '🎓' },
  { path: '/agent', label: 'Agent', icon: '🤖' },
];

const NavBar: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="nav">
      <div className="nav__inner">
        <NavLink to="/" className="nav__logo" onClick={() => setMobileOpen(false)}>
          <span className="nav__logo-icon">✨</span>
          <span className="nav__logo-text">Lite Agent Harness</span>
        </NavLink>

        <div className="nav__links">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `nav__link ${isActive ? 'nav__link--active' : ''}`
              }
            >
              <span className="nav__link-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className="nav__right">
          <GitHubStarButton />
          <button
            className="nav__hamburger"
            onClick={() => setMobileOpen(!mobileOpen)}
            type="button"
            aria-label="Toggle menu"
          >
            <span className={`nav__hamburger-line ${mobileOpen ? 'open' : ''}`} />
            <span className={`nav__hamburger-line ${mobileOpen ? 'open' : ''}`} />
            <span className={`nav__hamburger-line ${mobileOpen ? 'open' : ''}`} />
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="nav__mobile"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
          >
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `nav__mobile-link ${isActive ? 'nav__mobile-link--active' : ''}`
                }
                onClick={() => setMobileOpen(false)}
              >
                <span>{item.icon}</span> {item.label}
              </NavLink>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default NavBar;
