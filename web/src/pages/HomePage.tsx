import React from 'react';
import PageTransition from '../components/PageTransition';
import HeroSection from '../components/HeroSection';
import CardGrid from '../components/CardGrid';
import GitHubCommunity from '../components/GitHubCommunity';
import '../styles/home.css';

const HomePage: React.FC = () => (
  <PageTransition>
    <HeroSection />
    <CardGrid />
    <GitHubCommunity />
  </PageTransition>
);

export default HomePage;
