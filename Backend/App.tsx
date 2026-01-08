import React, { useEffect, useState } from 'react';
import { HashRouter } from 'react-router-dom';
import { fetchUsers, calculateScore, setApiBaseUrl, getApiBaseUrl } from './services/api';
import { User, FullUserPerformance } from './types';
import { DashboardOverview } from './components/DashboardOverview';
import { UserDetail } from './components/UserDetail';
import { LoginPage } from './components/LoginPage';
import { LayoutDashboard, Loader2, Users, WifiOff, ShieldAlert, Settings } from 'lucide-react';

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [performances, setPerformances] = useState<FullUserPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  
  // Settings for API connection
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());
  const [showSettings, setShowSettings] = useState(false);

  // Initial Load
  useEffect(() => {
    if (!isLoggedIn) return;
    loadData();
  }, [isLoggedIn]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Update the service with current URL state
      setApiBaseUrl(apiUrl);
      
      // 1. Fetch Users
      const usersList = await fetchUsers();
      setUsers(usersList);

      console.log(`Starting score calculation for ${usersList.length} users...`);

      // 2. Calculate scores in parallel
      const performancePromises = usersList.map(async (user): Promise<FullUserPerformance | null> => {
        try {
          const scoreData = await calculateScore(user.id);
          
          if (!scoreData || !scoreData.variables) {
             throw new Error(`Invalid data structure for ${user.id}`);
          }

          const calculatedScore = 
            (scoreData.variables.base_points * scoreData.variables.difficulty_factor) + 
            (scoreData.variables.peer_kudos_count * 1.5) - 
            scoreData.variables.blocker_penalty_total;
          
          return {
            ...user,
            ...scoreData,
            final_score: calculatedScore
          };
        } catch (e) {
          console.error(`Error processing user ${user.id}`, e);
          return null;
        }
      });

      const results = (await Promise.all(performancePromises))
        .filter((p): p is FullUserPerformance => p !== null);
      
      setPerformances(results);
      
      if (results.length === 0 && usersList.length > 0) {
         setError("Connected to User API, but failed to calculate scores. Check backend logs.");
      }

    } catch (error: any) {
      console.error("Failed to initialize dashboard", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    // Apply the URL from the input before retrying
    setApiBaseUrl(apiUrl);
    loadData();
  };

  const selectedUserPerformance = selectedUserId 
    ? performances.find(p => p.id === selectedUserId) 
    : null;

  if (!isLoggedIn) {
    return <LoginPage onLogin={() => setIsLoggedIn(true)} />;
  }

  return (
    <HashRouter>
      <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans selection:bg-blue-500/30">
        
        {/* Sidebar */}
        <aside className="w-64 bg-slate-950 border-r border-slate-800 hidden md:flex flex-col">
          <div className="p-6 border-b border-slate-800">
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-500 to-indigo-500 bg-clip-text text-transparent">
              WorkForce
            </h1>
            <p className="text-xs text-slate-500 mt-1">Contribution Manager</p>
          </div>
          
          <nav className="flex-1 p-4 space-y-2">
            <button 
              onClick={() => setSelectedUserId(null)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                !selectedUserId 
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20' 
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <LayoutDashboard size={18} />
              Overview
            </button>
            
            <div className="pt-4 pb-2">
              <p className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider">Team Members</p>
            </div>

            <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-300px)] custom-scrollbar">
              {users.map(user => (
                <button
                  key={user.id}
                  onClick={() => setSelectedUserId(user.id)}
                  className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-sm transition-colors ${
                    selectedUserId === user.id 
                      ? 'bg-slate-800 text-white' 
                      : 'text-slate-400 hover:bg-slate-900/50 hover:text-slate-300'
                  }`}
                >
                  <div className="w-6 h-6 rounded-full bg-slate-800 overflow-hidden shrink-0">
                    <img src={user.avatarUrl} alt="" className="w-full h-full object-cover opacity-80" />
                  </div>
                  <span className="truncate">{user.name}</span>
                </button>
              ))}
            </div>
          </nav>

          <div className="p-4 border-t border-slate-800">
            <div className="flex items-center gap-3 px-4 py-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-xs font-bold">
                AD
              </div>
              <div className="text-xs">
                <p className="text-white font-medium">Admin User</p>
                <p className="text-slate-500">Engineering Lead</p>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          
          {/* Mobile Header */}
          <header className="md:hidden flex items-center justify-between p-4 bg-slate-950 border-b border-slate-800">
            <h1 className="font-bold text-lg">WorkForce</h1>
            <button className="p-2 text-slate-400">
              <Users size={24} />
            </button>
          </header>

          <div className="flex-1 overflow-y-auto p-4 md:p-8 relative">
            {loading ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center animate-fade-in">
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin mb-4" />
                <p className="text-slate-400 text-sm animate-pulse">Syncing with API...</p>
                <p className="text-slate-600 text-xs mt-2">Connecting to {apiUrl}</p>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-6 animate-fade-in">
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-6">
                  <WifiOff className="text-red-500" size={32} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Connection Error</h3>
                <p className="text-slate-400 max-w-md mb-6">{error}</p>
                
                {/* API Settings Logic */}
                <div className="w-full max-w-sm bg-slate-800 p-4 rounded-lg mb-6 border border-slate-700">
                  <label className="block text-left text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wide">
                    API Server URL
                  </label>
                  <div className="flex gap-2">
                    <input 
                      type="text" 
                      value={apiUrl}
                      onChange={(e) => setApiUrl(e.target.value)}
                      className="flex-1 bg-slate-950 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                      placeholder="http://localhost:8000"
                    />
                  </div>
                  <p className="text-left text-xs text-slate-500 mt-2">
                    Try switching between <code>localhost</code> and <code>127.0.0.1</code>
                  </p>
                </div>

                <button 
                  onClick={handleRetry}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors shadow-lg shadow-blue-900/20 font-medium"
                >
                  Save URL & Retry
                </button>
              </div>
            ) : (
              <>
                {selectedUserId && selectedUserPerformance ? (
                  <UserDetail 
                    user={selectedUserPerformance} 
                    onBack={() => setSelectedUserId(null)} 
                  />
                ) : (
                  <DashboardOverview 
                    performances={performances} 
                    onSelectUser={setSelectedUserId} 
                  />
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </HashRouter>
  );
};

export default App;