import React from 'react';
import { AlertCircle, AlertTriangle, Info, ShieldAlert } from 'lucide-react';

export function RiskBadge({ level, size = 'sm' }) {
  const normLevel = (level || 'low').toLowerCase();

  const configs = {
    critical: {
      label: 'Critical',
      icon: ShieldAlert,
      classes: 'bg-red-50 text-red-700 border-red-200 ring-red-500/20',
      dotColor: 'bg-red-500',
    },
    high: {
      label: 'High',
      icon: AlertCircle,
      classes: 'bg-orange-50 text-orange-700 border-orange-200 ring-orange-500/20',
      dotColor: 'bg-orange-500',
    },
    medium: {
      label: 'Medium',
      icon: AlertTriangle,
      classes: 'bg-amber-50 text-amber-700 border-amber-200 ring-amber-500/20',
      dotColor: 'bg-amber-500',
    },
    low: {
      label: 'Low',
      icon: Info,
      classes: 'bg-slate-100 text-slate-700 border-slate-200 ring-slate-400/20',
      dotColor: 'bg-slate-400',
    },
  };

  const config = configs[normLevel] || configs.low;
  const Icon = config.icon;

  const sizeClasses = size === 'xs' 
    ? 'text-[11px] px-1.5 py-0.5 gap-1' 
    : size === 'md'
    ? 'text-xs px-2.5 py-1 gap-1.5 font-medium'
    : 'text-xs px-2 py-0.5 gap-1 font-medium';

  return (
    <span
      className={`inline-flex items-center rounded-md border font-sans tracking-tight ${config.classes} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor}`} />
      <span className="capitalize">{config.label}</span>
    </span>
  );
}

export function CategoryBadge({ category }) {
  const labels = {
    auto_renewal: 'Auto-renewal',
    hidden_fees: 'Hidden Fees',
    arbitration: 'Arbitration',
    data_sharing: 'Data Sharing',
    cancellation: 'Cancellation',
    data_retention: 'Data Retention',
    liability: 'Liability',
  };

  const cleanLabel = labels[category] || category?.replace(/_/g, ' ') || 'General';

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
      {cleanLabel}
    </span>
  );
}
