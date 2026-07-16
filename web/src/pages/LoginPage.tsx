import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';

const LoginPage: React.FC = () => {
  const { login } = useAuth();

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', background: 'var(--color-bg-primary)',
    }}>
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        style={{ textAlign: 'center' }}
      >
        <h1 className="gradient-text" style={{
          fontFamily: 'var(--font-display)', fontSize: 'var(--text-hero)',
          marginBottom: 16,
        }}>
          Glimmer
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: 32, fontSize: 'var(--text-lg)' }}>
          登录后开始使用
        </p>
        <button
          onClick={login}
          style={{
            padding: '14px 40px',
            background: 'var(--color-accent)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-full)',
            fontSize: 'var(--text-base)',
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: '0 0 20px rgba(248,164,200,0.3)',
            transition: 'all var(--transition-normal)',
          }}
        >
          Sign in with GitHub
        </button>
      </motion.div>
    </div>
  );
};

export default LoginPage;
