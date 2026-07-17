import { useState, useEffect } from 'react';

interface GitHubStats {
  stars: number;
  forks: number;
  loading: boolean;
}

const REPO = 'jeannie-jy/Glimmer';
const API = `https://api.github.com/repos/${REPO}`;

export function useGitHubStars(): GitHubStats {
  const [stats, setStats] = useState<GitHubStats>({
    stars: 0,
    forks: 0,
    loading: true,
  });

  useEffect(() => {
    fetch(API)
      .then((res) => res.json())
      .then((data) => {
        setStats({
          stars: data.stargazers_count ?? 0,
          forks: data.forks_count ?? 0,
          loading: false,
        });
      })
      .catch(() => {
        setStats((s) => ({ ...s, loading: false }));
      });
  }, []);

  return stats;
}
