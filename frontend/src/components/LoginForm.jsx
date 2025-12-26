import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User, AlertCircle } from 'lucide-react';

const LoginForm = () => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Hardcoded credentials check
    if (userId === 'alvintehg' && password === 'me1234') {
      // Store authentication state
      sessionStorage.setItem('isAuthenticated', 'true');
      sessionStorage.setItem('userId', userId);

      // Redirect to dashboard
      setTimeout(() => {
        navigate('/app');
      }, 500);
    } else {
      setLoading(false);
      setError('Invalid username or password. Please check your credentials and try again.');
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="glass-card-strong rounded-[20px] p-8 shadow-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-full gradient-blue-button flex items-center justify-center mx-auto mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-white tracking-wider mb-2" style={{ textTransform: 'uppercase' }}>
            Welcome Back
          </h2>
          <p className="text-white text-opacity-70">Sign in to access your financial dashboard</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500 bg-opacity-30 border-2 border-red-400 flex items-center gap-3 relative z-10">
            <AlertCircle className="w-5 h-5 text-red-300 flex-shrink-0" />
            <p className="text-white font-semibold text-sm">{error}</p>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* User ID Input */}
          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              User ID
            </label>
            <div className="relative">
              <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                <User className="w-5 h-5 text-white text-opacity-40" />
              </div>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="Enter your user ID"
                className="w-full pl-12 pr-4 py-3 rounded-xl bg-white bg-opacity-5 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-40 focus:outline-none focus:border-blue-500 focus:bg-opacity-10 transition-all duration-300"
                required
                disabled={loading}
              />
            </div>
          </div>

          {/* Password Input */}
          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Password
            </label>
            <div className="relative">
              <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                <Lock className="w-5 h-5 text-white text-opacity-40" />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full pl-12 pr-4 py-3 rounded-xl bg-white bg-opacity-5 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-40 focus:outline-none focus:border-blue-500 focus:bg-opacity-10 transition-all duration-300"
                required
                disabled={loading}
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 rounded-xl gradient-blue-button text-white font-semibold text-lg transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Signing In...</span>
              </div>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Footer Note */}
        <div className="mt-6 text-center">
          <p className="text-white text-opacity-50 text-xs">
            Secure access powered by WEALTH.AI
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
