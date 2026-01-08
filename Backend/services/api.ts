import { User, ScoreResponse, FullUserPerformance, AdvancedMetrics } from '../types';

// Default to localhost, but allow it to be changed dynamically
let API_BASE = 'http://localhost:8000';

export const setApiBaseUrl = (url: string) => {
  API_BASE = url.replace(/\/$/, ''); // Remove trailing slash
};

export const getApiBaseUrl = () => API_BASE;

/**
 * HYBRID API STRATEGY
 * Users are hardcoded as per provided data.
 * Scores are fetched from the real API.
 */

const PROVIDED_USER_IDS = [
  "alice-dev",
  "bob-backend",
  "charlie-frontend",
  "diana-ml",
  "ethan-arch"
];

// Feature 20: Historical Trend Generator
const generateHistory = (baseScore: number) => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  return months.map((m, i) => ({
    month: m,
    score: Math.max(0, baseScore + (Math.random() * 40 - 20) + (i * 2)) // Slight upward trend
  }));
};

// Deterministic simulation of advanced metrics based on user ID and Score
const generateAdvancedMetrics = (userId: string, baseScore: number): AdvancedMetrics => {
  const isDev = userId.includes('dev') || userId.includes('frontend') || userId.includes('backend');
  const isArch = userId.includes('arch');
  const isMl = userId.includes('ml');

  return {
    // Feature 1: Skill-Based Decomposition
    skills: [
      { name: 'Architecture', score: isArch ? 95 : 40, gap: isArch ? 0 : -20 },
      { name: 'Code Quality', score: isDev ? 90 : 70, gap: 5 },
      { name: 'DevOps', score: isDev ? 60 : 30, gap: -15 },
      { name: 'Communication', score: baseScore > 120 ? 85 : 60, gap: 0 },
      { name: 'Innovation', score: isMl ? 95 : 50, gap: 0 },
    ],
    // Feature 5: Project-Based Attribution
    projects: [
      { name: 'Project Alpha', impact_value: '$2M', role: 'Lead', contribution_pct: 45 },
      { name: 'Legacy Migration', impact_value: 'Efficiency', role: 'Contributor', contribution_pct: 20 },
    ],
    // Feature 2, 4, 13: Wellness & Dynamics
    wellness: {
      burnout_risk: baseScore > 150 ? 85 : 30, // High performers might be burning out
      async_efficiency: 8.5,
      timezone_load_balance: 'Optimal',
      last_break_taken: '2 hours ago'
    },
    // Feature 3, 14: Career Growth
    growth: {
      mentorship_score: isArch ? 9.2 : 4.5,
      learning_velocity: 8.8,
      promotion_readiness: baseScore > 130 ? 90 : 60,
      next_level_skills: ['Strategic Planning', 'Public Speaking']
    },
    // Feature 6: Innovation
    innovation_score: isMl ? 92 : 65,
    // Feature 9: Tech Debt
    tech_debt_reduction: isArch ? 450 : 120, // Hours saved
    // Feature 7: Customer Impact
    customer_impact: Math.floor(baseScore * 10), // Users affected
    // Feature 18: Attrition Risk
    attrition_risk_prediction: baseScore > 160 ? 'High' : 'Low', // Top talent flight risk
    // Feature 20: History
    score_history: generateHistory(baseScore)
  };
};

export const fetchUsers = async (): Promise<User[]> => {
  return Promise.resolve(PROVIDED_USER_IDS.map(id => {
    const parts = id.split('-');
    const name = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
    const role = parts.length > 1 ? parts[1].toUpperCase() : 'MEMBER';
    
    return {
      id: id,
      name: name,
      role: role,
      avatarUrl: undefined 
    };
  }));
};

export const calculateScore = async (userId: string): Promise<ScoreResponse & { advanced: AdvancedMetrics }> => {
  try {
    const response = await fetch(`${API_BASE}/calculate-score/${userId}`, {
      method: 'POST',
      mode: 'cors',
      credentials: 'omit',
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`POST /calculate-score/${userId} failed: ${response.status} - ${errorText}`);
    }
    
    const data = await response.json();
    
    // Calculate raw score locally to feed the generator
    const calculatedScore = 
      (data.variables.base_points * data.variables.difficulty_factor) + 
      (data.variables.peer_kudos_count * 1.5) - 
      data.variables.blocker_penalty_total;

    // Attach simulated advanced metrics
    return {
      ...data,
      advanced: generateAdvancedMetrics(userId, calculatedScore)
    };

  } catch (error: any) {
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error(`Network Error: Could not connect to ${API_BASE}. Check CORS or if server is running.`);
    }
    throw error;
  }
};