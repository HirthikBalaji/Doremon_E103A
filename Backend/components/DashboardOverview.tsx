import React, { useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  Cell, ReferenceLine 
} from 'recharts';
import { FullUserPerformance } from '../types';
import { Users, TrendingUp, Award, AlertTriangle, Download, Zap, Heart } from 'lucide-react';
import { MetricsCard } from './MetricsCard';

interface DashboardOverviewProps {
  performances: FullUserPerformance[];
  onSelectUser: (id: string) => void;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-900 border border-slate-700 p-3 rounded shadow-xl z-50">
        <p className="text-slate-200 font-bold mb-1">{label}</p>
        <p className="text-emerald-400 text-sm">Score: {data.score.toFixed(1)}</p>
        <p className="text-blue-400 text-xs mt-1">Innovation: {data.advanced?.innovation_score}</p>
        <p className={`text-xs mt-1 ${(data.advanced?.wellness.burnout_risk || 0) > 70 ? 'text-rose-400' : 'text-slate-400'}`}>
          Burnout Risk: {data.advanced?.wellness.burnout_risk}%
        </p>
      </div>
    );
  }
  return null;
};

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ performances, onSelectUser }) => {
  const topPerformer = useMemo(() => {
    if (performances.length === 0) return null;
    return performances.reduce((prev, current) => 
      (prev.final_score > current.final_score) ? prev : current
    );
  }, [performances]);

  const totalKudos = useMemo(() => 
    performances.reduce((acc, curr) => acc + curr.variables.peer_kudos_count, 0),
  [performances]);

  const avgScore = useMemo(() => {
    if (performances.length === 0) return 0;
    const sum = performances.reduce((acc, curr) => acc + curr.final_score, 0);
    return (sum / performances.length).toFixed(1);
  }, [performances]);

  // Feature 4: Aggregate Burnout
  const highBurnoutRisk = useMemo(() => 
    performances.filter(p => (p.advanced?.wellness.burnout_risk || 0) > 70).length,
  [performances]);

  const chartData = performances.map(p => ({
    name: p.name.split(' ')[0],
    score: p.final_score,
    id: p.id,
    ...p
  })).sort((a, b) => b.score - a.score);

  const handleExportCSV = () => {
    if (performances.length === 0) return;

    const headers = [
      "User ID", "Name", "Role", "Final Score", 
      "Innovation Score", "Burnout Risk", "Tech Debt Removed", "Promotion Readiness"
    ];

    const rows = performances.map(p => [
      p.id, `"${p.name}"`, `"${p.role}"`, p.final_score.toFixed(2),
      p.advanced?.innovation_score || 0,
      p.advanced?.wellness.burnout_risk || 0,
      p.advanced?.tech_debt_reduction || 0,
      p.advanced?.growth.promotion_readiness || 0
    ]);

    const csvContent = [headers.join(","), ...rows.map(row => row.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `workforce_advanced_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
           <h2 className="text-2xl font-bold text-white">Performance Overview</h2>
           <p className="text-slate-400 text-sm">Real-time contribution & wellness metrics</p>
        </div>
        <button 
          onClick={handleExportCSV}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-900/20"
        >
          <Download size={16} />
          Export Advanced Data
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard 
          title="Avg Team Score" 
          value={avgScore} 
          icon={<TrendingUp size={24} />} 
          color="blue"
          trend="Based on 20+ metrics"
        />
        <MetricsCard 
          title="Burnout Alert" 
          value={highBurnoutRisk} 
          icon={<Heart size={24} />} 
          color={highBurnoutRisk > 0 ? "red" : "green"}
          trend="Members at high risk"
        />
        <MetricsCard 
          title="Total Kudos" 
          value={totalKudos} 
          icon={<Users size={24} />} 
          color="green"
          trend="Peer recognition count"
        />
        <MetricsCard 
          title="Innovation Index" 
          value="8.4" 
          icon={<Zap size={24} />} 
          color="purple"
          trend="Team experimentation rate"
        />
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 shadow-sm">
        <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-slate-100">Team Contribution Leaderboard</h2>
            <div className="flex gap-2 text-xs text-slate-500">
               <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-blue-500"></div> Score</span>
               <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-rose-500"></div> High Burnout</span>
            </div>
        </div>
        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis 
                dataKey="name" 
                stroke="#94a3b8" 
                tick={{ fill: '#94a3b8' }} 
                axisLine={{ stroke: '#475569' }}
              />
              <YAxis 
                stroke="#94a3b8" 
                tick={{ fill: '#94a3b8' }} 
                axisLine={{ stroke: '#475569' }}
              />
              <Tooltip cursor={{fill: '#334155', opacity: 0.2}} content={<CustomTooltip />} />
              <ReferenceLine y={100} stroke="#f59e0b" strokeDasharray="3 3" label={{ position: 'right', value: 'Base', fill: '#f59e0b', fontSize: 12 }} />
              <Bar dataKey="score" radius={[6, 6, 0, 0]} onClick={(data) => onSelectUser(data.id)} className="cursor-pointer">
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    // Feature 4: Visual burnout indicator on the main chart
                    fill={(entry.advanced?.wellness.burnout_risk || 0) > 70 ? '#f43f5e' : '#3b82f6'} 
                    className="transition-all duration-300 hover:opacity-80"
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="text-center text-slate-500 text-sm mt-4">
          Click on a bar to view detailed Skill, Wellness, and Impact analysis.
        </p>
      </div>
    </div>
  );
};