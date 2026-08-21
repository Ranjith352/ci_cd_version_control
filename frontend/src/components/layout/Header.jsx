import React from 'react';

export const Header = ({ title = 'Environmental Intelligence Dashboard' }) => {
  return (
    <header className="top-header">
      <h1 className="header-title">{title}</h1>
      <div className="header-status">
        <span className="status-dot"></span>
        <span>FastAPI Connected</span>
      </div>
    </header>
  );
};

export default Header;
