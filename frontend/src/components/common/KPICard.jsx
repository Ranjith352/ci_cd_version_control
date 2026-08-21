import React from 'react';

export const KPICard = ({ title, value, subtext, icon: Icon, color = 'var(--primary)' }) => {
  return (
    <div className="kpi-card">
      <div>
        <div className="kpi-title">{title}</div>
        <div className="kpi-value">{value}</div>
        {subtext && <div className="kpi-subtext">{subtext}</div>}
      </div>
      {Icon && (
        <div className="kpi-icon" style={{ backgroundColor: `${color}20`, color: color }}>
          <Icon size={22} />
        </div>
      )}
    </div>
  );
};

export default KPICard;
