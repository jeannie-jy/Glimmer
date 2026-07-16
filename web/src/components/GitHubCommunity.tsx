import React from 'react';
import { motion } from 'framer-motion';
import { useGitHubStars } from '../hooks/useGitHubStars';

const REPO_URL = 'https://github.com/jingyu-wang/lite-agent-harness';

const GitHubCommunity: React.FC = () => {
  const { stars, forks, loading } = useGitHubStars();

  return (
    <section className="github-community">
      <div className="github-community__bg" />
      <motion.div
        className="github-community__content"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="github-community__title">🌟 开源魔法，众人共创</h2>

        {!loading && (
          <motion.div
            className="github-community__stats"
            initial={{ scale: 0.8 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
          >
            <span className="github-community__stat">⭐ {stars.toLocaleString()} Stars</span>
            <span className="github-community__stat">🍴 {forks.toLocaleString()} Forks</span>
          </motion.div>
        )}

        <div className="github-community__actions">
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="github-community__btn github-community__btn--primary">
            ⭐ Star on GitHub
          </a>
          <a href={`${REPO_URL}/issues`} target="_blank" rel="noopener noreferrer" className="github-community__btn github-community__btn--secondary">
            📋 View Issues
          </a>
        </div>
      </motion.div>
    </section>
  );
};

export default GitHubCommunity;
