// API Configuration
// In development, when accessing via browser, use localhost:5001
// In production or container environment, use the environment variable
const getApiBaseUrl = () => {
  // If we're in a browser environment and accessing localhost:3000, use localhost:5001
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:5001';
  }

  // Otherwise use environment variable or fallback
  return process.env.REACT_APP_API_URL || 'http://localhost:5001';
};

const API_BASE_URL = getApiBaseUrl();

export const apiConfig = {
  baseURL: API_BASE_URL,
  endpoints: {
    dashboard: {
      overview: '/api/dashboard/overview',
      evolucaoTemporal: '/api/dashboard/evolucao-temporal',
      fontesTrafico: '/api/dashboard/fontes-trafico',
      distribuicaoHoraria: '/api/dashboard/distribuicao-horaria',
      topCidades: '/api/dashboard/top-cidades',
      topProvedores: '/api/dashboard/top-provedores',
      leads: '/api/dashboard/leads'
    },
    theme: {
      config: '/api/theme/config'
    },
    domain: {
      info: '/api/domain/info'
    }
  }
};

// Helper function to build full URL
export const buildApiUrl = (endpoint, params = '') => {
  return `${API_BASE_URL}${endpoint}${params}`;
};

// Helper function to add domain header for multi-domain support
export const getDomainHeaders = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const domain = urlParams.get('domain');

  console.log('Domain detection:', {
    url: window.location.href,
    search: window.location.search,
    domain: domain
  });

  if (domain) {
    console.log('Adding X-Domain header:', domain);
    return {
      'X-Domain': domain
    };
  }

  console.log('No domain parameter, using default');
  return {};
};

export default apiConfig;