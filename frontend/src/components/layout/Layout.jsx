import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export const Layout = ({ pageTitle }) => {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Header title={pageTitle} />
        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
