import React, { useState } from 'react';
import { LayoutDashboard, Lock, Mail, ArrowRight, Loader2 } from 'lucide-react';

interface LoginPageProps {
  onLogin: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      onLogin();
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[100px]"></div>
        <div className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[100px]"></div>
      </div>

      <div className="w-full max-w-md bg-slate-900/50 backdrop-blur-xl border border-slate-800 p-8 rounded-2xl shadow-2xl relative z-10 animate-fade-in-up">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20">
            <LayoutDashboard className="text-white" size={24} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Welcome back</h1>
          <p className="text-slate-400 text-sm mt-2">Sign in to WorkForce Analytics</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider ml-1">Email Address</label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-slate-500 group-focus-within:text-blue-400 transition-colors" />
              </div>
              <input 
                type="email" 
                required
                className="block w-full pl-10 pr-3 py-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                placeholder="admin@workforce.com"
                defaultValue="admin@workforce.com"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider ml-1">Password</label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-slate-500 group-focus-within:text-blue-400 transition-colors" />
              </div>
              <input 
                type="password" 
                required
                className="block w-full pl-10 pr-3 py-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                placeholder="••••••••"
                defaultValue="password"
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold py-3 px-4 rounded-lg transition-all transform active:scale-[0.98] shadow-lg shadow-blue-900/20 disabled:opacity-70 disabled:cursor-not-allowed mt-6"
          >
            {isLoading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <>
                Sign In <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>
        
        <p className="mt-6 text-center text-xs text-slate-500">
          Protected by enterprise-grade encryption. <br/>
          <span className="hover:text-slate-400 cursor-pointer transition-colors">Forgot password?</span>
        </p>
      </div>
    </div>
  );
};