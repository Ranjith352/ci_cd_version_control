import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Wind, Activity, ShieldCheck } from 'lucide-react';

export const Sidebar = () => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <ShieldCheck size={28} color="var(--primary)" />
        <span className="sidebar-title">Environmental Intelligence</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
          <LayoutDashboard size={20} />
          <span>Dashboard</span>
        </NavLink>

        <NavLink to="/air-quality" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Wind size={20} />
          <span>Air Quality</span>
        </NavLink>

        <NavLink to="/earthquakes" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Activity size={20} />
          <span>Earthquakes</span>
        </NavLink>
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
        <div>FastAPI & Prefect Pipeline</div>
        <div>v1.0.0 • Batch Dashboard</div>
      </div>
    </aside>
  );
};

export default Sidebar;
