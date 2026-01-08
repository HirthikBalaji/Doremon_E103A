import React from 'react';

interface MetricsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: string;
  color?: string;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({ title, value, icon, trend, color = "blue" }) => {
  const colorClasses: Record<string, string> = {
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    green: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    red: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  };

  const selectedColor = colorClasses[color] || colorClasses.blue;

  return (
    <div className={`p-6 rounded-xl border ${selectedColor.split(' ')[2]} bg-slate-800/50 backdrop-blur-sm shadow-sm transition-all duration-300 hover:shadow-md hover:translate-y-[-2px]`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-slate-400 text-sm font-medium uppercase tracking-wider">{title}</p>
          <h3 className="text-3xl font-bold mt-2 text-white">{value}</h3>
        </div>
        <div className={`p-3 rounded-lg ${selectedColor}`}>
          {icon}
        </div>
      </div>
      {trend && (
        <p className="mt-4 text-xs font-medium text-slate-500">
          {trend}
        </p>
      )}
    </div>
  );
};