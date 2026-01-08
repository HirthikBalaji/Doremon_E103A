import React, { useState } from 'react';
import { FullUserPerformance } from '../types';
import { 
  ArrowLeft, ThumbsUp, AlertOctagon, BrainCircuit, Activity, 
  Target, ShieldAlert, Zap, Clock, Heart, TrendingUp, Users, 
  GitCommit, Briefcase, Award, Rocket
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, 
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  LineChart, Line, XAxis, YAxis, CartesianGrid, AreaChart, Area
} from 'recharts';

interface UserDetailProps {
  user: FullUserPerformance;
  onBack: () => void;
}

export const UserDetail: React.FC<UserDetailProps> = ({ user, onBack }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'skills' | 'wellness' | 'impact'>('overview');
  const { variables, analysis_summary, final_score, advanced } = user;
  
  // Basic Formula
  const difficultyScore = variables.base_points * variables.difficulty_factor;
  const kudosScore = variables.peer_kudos_count * 1.5;
  const penaltyScore = variables.blocker_penalty_total;

  // Chart Data
  const pieData = [
    { name: 'Base Difficulty', value: difficultyScore, color: '#3b82f6' },
    { name: 'Peer Kudos', value: kudosScore, color: '#10b981' },
    { name: 'Penalty', value: penaltyScore, color: '#ef4444' },
  ];

  const radarData = advanced?.skills.map(s => ({
    subject: s.name,
    A: s.score,
    fullMark: 100
  })) || [];

  const TabButton = ({ id, label, icon: Icon }: any) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
        activeTab === id 
          ? 'border-blue-500 text-blue-400 bg-blue-500/5' 
          : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
      }`}
    >
      <Icon size={16} />
      {label}
    </button>
  );

  return (
    <div className="space-y-6 animate-fade-in-up h-full flex flex-col">
      <div className="flex items-center justify-between shrink-0">
        <button 
          onClick={onBack}
          className="flex items-center text-slate-400 hover:text-white transition-colors gap-2 text-sm font-medium"
        >
          <ArrowLeft size={16} /> Back to Team
        </button>
        
        {/* Feature 18: Attrition Risk Indicator */}
        {advanced?.attrition_risk_prediction === 'High' && (
          <div className="flex items-center gap-2 px-3 py-1 bg-rose-500/20 text-rose-400 rounded-full text-xs font-bold border border-rose-500/30 animate-pulse">
            <ShieldAlert size={14} /> High Retention Risk
          </div>
        )}
      </div>

      {/* User Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-800 rounded-2xl p-6 border border-slate-700 shadow-lg shrink-0">
        <div className="flex items-center gap-4">
          <div className="relative">
            <img 
              src={user.avatarUrl || `https://ui-avatars.com/api/?name=${user.name}`} 
              alt={user.name} 
              className="w-16 h-16 rounded-full border-2 border-slate-600"
            />
            {/* Feature 14: Level Badge */}
            <div className="absolute -bottom-1 -right-1 bg-indigo-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full border border-slate-800">
              L{Math.floor(final_score / 50) + 1}
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">{user.name}</h1>
            <div className="flex items-center gap-2 text-slate-400 text-sm">
              <Briefcase size={14} />
              {user.role} 
              <span className="text-slate-600">•</span>
              {/* Feature 2: Timezone */}
              <Clock size={14} />
              UTC-5 (EST)
            </div>
          </div>
        </div>
        <div className="mt-4 md:mt-0 text-right">
          <p className="text-slate-400 text-xs uppercase tracking-wide font-semibold">Current Impact Score</p>
          <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            {final_score.toFixed(0)}
          </div>
          {/* Feature 20: Trend Indicator */}
          <div className="flex items-center justify-end gap-1 text-emerald-400 text-xs mt-1">
             <TrendingUp size={12} /> +12% vs last month
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700 bg-slate-900/50 sticky top-0 z-10 backdrop-blur-md">
        <TabButton id="overview" label="Overview" icon={Activity} />
        <TabButton id="skills" label="Skills & Growth" icon={BrainCircuit} />
        <TabButton id="wellness" label="Wellness & Dynamics" icon={Heart} />
        <TabButton id="impact" label="Impact & Strategy" icon={Rocket} />
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-6">
        
        {/* --- OVERVIEW TAB --- */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in">
            {/* Score Breakdown */}
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                <h3 className="text-lg font-semibold text-white mb-4">Score Composition</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 relative overflow-hidden">
                       <div className="absolute top-0 right-0 p-2 opacity-10"><Target size={40} /></div>
                       <div className="text-slate-400 text-xs uppercase mb-1">Base × Difficulty</div>
                       <div className="text-2xl font-bold text-blue-400">{difficultyScore.toFixed(0)}</div>
                       <div className="text-xs text-slate-500 mt-1">Factor: {variables.difficulty_factor}x</div>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 relative overflow-hidden">
                       <div className="absolute top-0 right-0 p-2 opacity-10"><ThumbsUp size={40} /></div>
                       <div className="text-slate-400 text-xs uppercase mb-1">Peer Kudos</div>
                       <div className="text-2xl font-bold text-emerald-400">+{kudosScore.toFixed(0)}</div>
                       <div className="text-xs text-slate-500 mt-1">Count: {variables.peer_kudos_count}</div>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 relative overflow-hidden">
                       <div className="absolute top-0 right-0 p-2 opacity-10"><AlertOctagon size={40} /></div>
                       <div className="text-slate-400 text-xs uppercase mb-1">Penalties</div>
                       <div className="text-2xl font-bold text-rose-400">-{penaltyScore}</div>
                       <div className="text-xs text-slate-500 mt-1">Blockers</div>
                    </div>
                </div>

                <div className="bg-slate-900/30 p-4 rounded-lg border-l-4 border-blue-500">
                   <h4 className="text-sm font-bold text-white mb-1">Difficulty Rationale</h4>
                   <p className="text-slate-400 text-sm italic">"{analysis_summary.difficulty_rationale}"</p>
                </div>
              </div>

              {/* Feature 20: History Chart */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50 h-[300px]">
                <h3 className="text-lg font-semibold text-white mb-4">6-Month Trend</h3>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={advanced?.score_history}>
                    <defs>
                      <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="month" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                    <Area type="monotone" dataKey="score" stroke="#3b82f6" fillOpacity={1} fill="url(#colorScore)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50 h-[300px]">
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Contribution Mix</h3>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                      ))}
                    </Pie>
                    <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Evidence Feed */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50 max-h-[400px] overflow-y-auto custom-scrollbar">
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Evidence Log</h3>
                <ul className="space-y-4">
                  {analysis_summary.kudos_evidence.map((ev, i) => (
                    <li key={`k-${i}`} className="text-sm text-slate-400 bg-slate-900/50 p-3 rounded border border-emerald-500/20">
                      <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1 text-xs">
                        <ThumbsUp size={12} /> PEER KUDOS
                      </div>
                      {ev}
                    </li>
                  ))}
                  {analysis_summary.penalty_evidence.map((ev, i) => (
                    <li key={`p-${i}`} className="text-sm text-slate-400 bg-slate-900/50 p-3 rounded border border-rose-500/20">
                      <div className="flex items-center gap-2 text-rose-400 font-semibold mb-1 text-xs">
                         <AlertOctagon size={12} /> PENALTY
                      </div>
                      {ev}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* --- SKILLS TAB --- */}
        {activeTab === 'skills' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
            {/* Feature 1: Skill Radar */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50 h-[400px]">
              <h3 className="text-lg font-semibold text-white mb-4">Skill Decomposition</h3>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name="Skills" dataKey="A" stroke="#8b5cf6" strokeWidth={2} fill="#8b5cf6" fillOpacity={0.3} />
                  <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-6">
              {/* Feature 14: Career Growth */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                <h3 className="text-lg font-semibold text-white mb-4">Career Trajectory</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-400">Promotion Readiness</span>
                      <span className="text-white font-bold">{advanced?.growth.promotion_readiness}%</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-blue-500 to-indigo-500" style={{ width: `${advanced?.growth.promotion_readiness}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-400">Learning Velocity</span>
                      <span className="text-white font-bold">{advanced?.growth.learning_velocity}/10</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: `${(advanced?.growth.learning_velocity || 0) * 10}%` }}></div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Recommended Next Steps</h4>
                  <div className="flex flex-wrap gap-2">
                    {advanced?.growth.next_level_skills.map(skill => (
                      <span key={skill} className="px-3 py-1 bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 rounded-full text-xs">
                        + {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Feature 3: Mentorship */}
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50 flex items-center justify-between">
                 <div>
                    <h3 className="text-sm font-semibold text-slate-400">Mentorship Score</h3>
                    <p className="text-xs text-slate-500 mt-1">Impact on junior team members</p>
                 </div>
                 <div className="flex items-center gap-2">
                    <span className="text-3xl font-bold text-white">{advanced?.growth.mentorship_score}</span>
                    <Users size={20} className="text-blue-400" />
                 </div>
              </div>
            </div>
          </div>
        )}

        {/* --- WELLNESS TAB --- */}
        {activeTab === 'wellness' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
             {/* Feature 4: Burnout Indicator */}
             <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-semibold text-white">Burnout Risk</h3>
                  <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                    (advanced?.wellness.burnout_risk || 0) > 70 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {(advanced?.wellness.burnout_risk || 0) > 70 ? 'ATTENTION REQUIRED' : 'HEALTHY'}
                  </div>
                </div>
                
                <div className="relative pt-4 pb-8">
                   <div className="h-4 bg-slate-700 rounded-full overflow-hidden flex">
                      <div className="w-1/3 bg-emerald-500/50"></div>
                      <div className="w-1/3 bg-amber-500/50"></div>
                      <div className="w-1/3 bg-rose-500/50"></div>
                   </div>
                   <div 
                      className="absolute top-2 w-1 h-8 bg-white border-2 border-slate-900 shadow-lg transform -translate-x-1/2 transition-all duration-500"
                      style={{ left: `${advanced?.wellness.burnout_risk}%` }}
                   ></div>
                   <div className="flex justify-between text-xs text-slate-500 mt-2">
                      <span>Low Risk</span>
                      <span>Moderate</span>
                      <span>Critical</span>
                   </div>
                </div>
                <p className="text-sm text-slate-400 bg-slate-900/50 p-3 rounded">
                   Last break taken: <span className="text-white">{advanced?.wellness.last_break_taken}</span>
                </p>
             </div>

             {/* Feature 2: Async Work */}
             <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                <h3 className="text-lg font-semibold text-white mb-4">Work Dynamics</h3>
                <div className="space-y-4">
                   <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                      <div className="flex items-center gap-3">
                         <Zap className="text-amber-400" size={20} />
                         <div>
                            <p className="text-sm font-medium text-white">Async Efficiency</p>
                            <p className="text-xs text-slate-500">Unblocking others without meetings</p>
                         </div>
                      </div>
                      <span className="text-xl font-bold text-white">{advanced?.wellness.async_efficiency}/10</span>
                   </div>

                   <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                      <div className="flex items-center gap-3">
                         <Clock className="text-blue-400" size={20} />
                         <div>
                            <p className="text-sm font-medium text-white">Timezone Load</p>
                            <p className="text-xs text-slate-500">Meeting overlap burden</p>
                         </div>
                      </div>
                      <span className="text-sm font-bold text-emerald-400">{advanced?.wellness.timezone_load_balance}</span>
                   </div>
                </div>
             </div>
          </div>
        )}

        {/* --- IMPACT TAB --- */}
        {activeTab === 'impact' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
             {/* Feature 5: Projects */}
             <div className="md:col-span-2 bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                <h3 className="text-lg font-semibold text-white mb-4">Project Impact Attribution</h3>
                <div className="space-y-3">
                   {advanced?.projects.map((proj, i) => (
                      <div key={i} className="flex items-center justify-between bg-slate-900/50 p-4 rounded-lg border border-slate-700/50">
                         <div>
                            <h4 className="text-white font-medium flex items-center gap-2">
                               <GitCommit size={16} className="text-blue-500" />
                               {proj.name}
                            </h4>
                            <p className="text-xs text-slate-400 mt-1">{proj.role} • {proj.contribution_pct}% Contribution</p>
                         </div>
                         <div className="text-right">
                            <div className="text-emerald-400 font-bold">{proj.impact_value}</div>
                            <div className="text-xs text-slate-500">Business Value</div>
                         </div>
                      </div>
                   ))}
                </div>
             </div>

             {/* KPIs */}
             <div className="space-y-4">
                {/* Feature 6: Innovation */}
                <div className="bg-gradient-to-br from-indigo-900/50 to-purple-900/50 p-6 rounded-xl border border-indigo-500/30">
                   <div className="flex justify-between items-start mb-2">
                      <h4 className="text-indigo-200 font-semibold">Innovation Score</h4>
                      <Rocket size={20} className="text-indigo-400" />
                   </div>
                   <div className="text-4xl font-bold text-white">{advanced?.innovation_score}</div>
                   <p className="text-xs text-indigo-300 mt-1">Experimentation & Risk Taking</p>
                </div>

                {/* Feature 9: Tech Debt */}
                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700/50">
                   <div className="flex justify-between items-start mb-2">
                      <h4 className="text-slate-300 font-semibold">Tech Debt Removed</h4>
                      <ShieldAlert size={20} className="text-slate-400" />
                   </div>
                   <div className="text-3xl font-bold text-white">{advanced?.tech_debt_reduction}h</div>
                   <p className="text-xs text-slate-500 mt-1">Maintenance hours saved</p>
                </div>

                {/* Feature 7: Customer Impact */}
                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700/50">
                   <div className="flex justify-between items-start mb-2">
                      <h4 className="text-slate-300 font-semibold">Customer Impact</h4>
                      <Users size={20} className="text-slate-400" />
                   </div>
                   <div className="text-3xl font-bold text-white">{advanced?.customer_impact}</div>
                   <p className="text-xs text-slate-500 mt-1">Users affected by code</p>
                </div>
             </div>
          </div>
        )}

      </div>
    </div>
  );
};