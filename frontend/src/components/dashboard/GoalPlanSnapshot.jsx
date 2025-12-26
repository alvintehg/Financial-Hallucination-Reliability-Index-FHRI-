import React, { useState, useEffect } from 'react';
import { Target, TrendingUp } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Goal Plan Snapshot - Shows nearest active financial goal
 * Displays target vs actual progress bar
 */
export const GoalPlanSnapshot = () => {
  const [goalData, setGoalData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchGoalData();
  }, []);

  const fetchGoalData = async () => {
    setLoading(true);
    try {
      // Example: Retirement goal of $1M in 20 years
      const response = await axios.post(`${API_BASE_URL}/planning/goal`, {
        target_amount: 1000000,
        years: 20,
        init_capital: 50000,
        monthly_contrib: null,  // Will calculate required amount
        expected_return: 0.07
      });
      setGoalData(response.data);
    } catch (error) {
      console.error('Error fetching goal data:', error);
      // Mock fallback data
      setGoalData({
        target_amount: 1000000,
        required_monthly: 1500,
        final_value: 980000,
        will_reach_goal: false,
        years: 20
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading || !goalData) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-white bg-opacity-5">
        <Target className="w-8 h-8 text-blue-400 animate-pulse" />
        <div className="flex-1">
          <div className="h-4 bg-white bg-opacity-10 rounded mb-2 animate-pulse"></div>
          <div className="h-2 bg-white bg-opacity-10 rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  const progressPct = (goalData.final_value / goalData.target_amount) * 100;
  const isOnTrack = goalData.will_reach_goal;

  return (
    <div className="p-4 rounded-xl bg-white bg-opacity-5 border border-white border-opacity-10">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Target className={`w-5 h-5 ${isOnTrack ? 'text-green-400' : 'text-orange-400'}`} />
          <h4 className="font-semibold text-white text-sm">Retirement Goal</h4>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${isOnTrack ? 'bg-green-500 bg-opacity-20 text-green-400' : 'bg-orange-500 bg-opacity-20 text-orange-400'}`}>
          {isOnTrack ? 'On Track' : 'Needs Adjustment'}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-white text-opacity-70 mb-1">
          <span>Progress</span>
          <span>{progressPct.toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-white bg-opacity-10 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${isOnTrack ? 'bg-gradient-to-r from-green-500 to-green-400' : 'bg-gradient-to-r from-orange-500 to-orange-400'}`}
            style={{ width: `${Math.min(progressPct, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Target vs Actual */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-xs text-white text-opacity-60 mb-1">Target</div>
          <div className="text-sm font-bold text-white">
            ${(goalData.target_amount / 1000).toFixed(0)}K
          </div>
        </div>
        <div>
          <div className="text-xs text-white text-opacity-60 mb-1">Projected</div>
          <div className="text-sm font-bold text-white">
            ${(goalData.final_value / 1000).toFixed(0)}K
          </div>
        </div>
      </div>

      {/* Monthly Contribution */}
      <div className="mt-3 pt-3 border-t border-white border-opacity-10">
        <div className="flex items-center justify-between text-xs">
          <span className="text-white text-opacity-70">Monthly Contribution</span>
          <span className="font-semibold text-white">${goalData.required_monthly?.toFixed(0)}/mo</span>
        </div>
      </div>
    </div>
  );
};
