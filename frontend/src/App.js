import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useThemeContext } from './contexts/ThemeContext';
import { buildApiUrl, getDomainHeaders } from './config/api';

function App() {
  const [activeTab, setActiveTab] = useState('evolucao');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    city: '',
    provider: ''
  });

  const [error, setError] = useState(null);

  // Use theme context
  const {
    themeConfig,
    loading: themeLoading,
    error: themeError,
    getThemeColors,
    getClientName,
    retryFetch: retryTheme,
    isLegacyMode,
    isFallbackMode
  } = useThemeContext();

  // Get dynamic colors from theme
  const themeColors = getThemeColors();
  const COLORS = themeColors.accents.length > 0 ? themeColors.accents : [themeColors.primary, themeColors.secondary];
  const clientName = getClientName();

  // Função para buscar dados da API
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Construir parâmetros de filtro
      const params = new URLSearchParams();
      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.city) params.append('city', filters.city);
      if (filters.provider) params.append('provider', filters.provider);

      const queryString = params.toString();
      const urlSuffix = queryString ? `?${queryString}` : '';

      // Get domain parameter for multi-domain support
      const urlParams = new URLSearchParams(window.location.search);
      const domain = urlParams.get('domain');

      // Add domain to URL parameters instead of headers
      let finalUrlSuffix = urlSuffix;
      if (domain) {
        const separator = urlSuffix ? '&' : '?';
        finalUrlSuffix = urlSuffix + separator + `domain=${encodeURIComponent(domain)}`;
      }



      // Buscar dados de diferentes endpoints
      const [overviewRes, evolucaoRes, traficoRes, horarioRes, cidadesRes, provedoresRes, leadsRes] = await Promise.all([
        fetch(buildApiUrl(`/api/dashboard/overview${finalUrlSuffix}`)),
        fetch(buildApiUrl(`/api/dashboard/evolucao-temporal${finalUrlSuffix}`)),
        fetch(buildApiUrl(`/api/dashboard/fontes-trafico${finalUrlSuffix}`)),
        fetch(buildApiUrl(`/api/dashboard/distribuicao-horaria${finalUrlSuffix}`)),
        fetch(buildApiUrl(`/api/dashboard/top-cidades${finalUrlSuffix}`)),
        fetch(buildApiUrl(`/api/dashboard/top-provedores${finalUrlSuffix}`)),
        fetch(buildApiUrl(`/api/dashboard/leads${finalUrlSuffix}`))
      ]);

      // Verificar se todas as respostas foram bem-sucedidas
      const responses = [overviewRes, evolucaoRes, traficoRes, horarioRes, cidadesRes, provedoresRes, leadsRes];
      const failedResponses = responses.filter(res => !res.ok);

      if (failedResponses.length > 0) {
        throw new Error('Erro ao carregar dados da API');
      }

      const overview = await overviewRes.json();
      const evolucaoTemporal = await evolucaoRes.json();
      const fontesTrafico = await traficoRes.json();
      const distribuicaoHoraria = await horarioRes.json();
      const topCidades = await cidadesRes.json();
      const topProvedores = await provedoresRes.json();
      const leadsData = await leadsRes.json();

      // Verificar se algum endpoint retornou erro
      const dataWithErrors = [overview, evolucaoTemporal, fontesTrafico, distribuicaoHoraria, topCidades, topProvedores, leadsData];
      const errorResponses = dataWithErrors.filter(data => data.error);

      if (errorResponses.length > 0) {
        throw new Error(errorResponses[0].error);
      }

      setData({
        overview,
        evolucaoTemporal,
        fontesTrafico,
        distribuicaoHoraria,
        topCidades,
        topProvedores,
        leads: leadsData.leads || []
      });

    } catch (error) {
      console.error('Erro ao buscar dados:', error);
      setError(error.message || 'Erro ao carregar dados da planilha');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const tabs = [
    { id: 'evolucao', label: 'Evolução Temporal', icon: '📈' },
    { id: 'trafico', label: 'Fontes de Tráfego', icon: '🎯' },
    { id: 'horario', label: 'Distribuição Horária', icon: '⏰' },
    { id: 'cidades', label: 'Top Cidades', icon: '🌍' },
    { id: 'provedores', label: 'Top Provedores', icon: '📡' },
    { id: 'leads', label: 'Lista de Leads', icon: '👥' }
  ];

  const downloadCSV = () => {
    if (!data?.leads) return;

    const csvContent = [
      ['Nome', 'Email', 'Telefone', 'Cidade', 'Provedor', 'Canal', 'Data'],
      ...data.leads.map(lead => [
        lead.nome, lead.email, lead.telefone, lead.cidade, lead.provedor, lead.canal, lead.data
      ])
    ].map(row => row.join(',')).join('\\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'leads_desktop.csv';
    a.click();
  };

  const renderContent = () => {
    // Show theme loading if theme is still loading
    if (themeLoading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 theme-spinner"></div>
          <span className="ml-4 text-gray-600">Carregando configuração do tema...</span>
        </div>
      );
    }

    // Show theme error if theme failed to load
    if (themeError && !isFallbackMode) {
      return (
        <div className="flex flex-col justify-center items-center h-64 bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="text-yellow-600 text-6xl mb-4">⚠️</div>
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">Erro no Tema</h3>
          <p className="text-yellow-600 text-center mb-4 max-w-md">{themeError}</p>
          <p className="text-sm text-yellow-600 text-center mb-4">Usando tema padrão temporariamente</p>
          <button
            onClick={retryTheme}
            className="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700 transition-colors"
          >
            Tentar Novamente
          </button>
        </div>
      );
    }

    if (loading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 theme-spinner"></div>
          <span className="ml-4 text-gray-600">Carregando dados da planilha...</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col justify-center items-center h-64 bg-red-50 rounded-lg border border-red-200">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h3 className="text-lg font-semibold text-red-800 mb-2">Erro ao Carregar Dados</h3>
          <p className="text-red-600 text-center mb-4 max-w-md">{error}</p>
          <button
            onClick={fetchData}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
          >
            Tentar Novamente
          </button>
        </div>
      );
    }

    if (!data) {
      return (
        <div className="flex flex-col justify-center items-center h-64 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-gray-400 text-6xl mb-4">📊</div>
          <h3 className="text-lg font-semibold text-gray-600 mb-2">Nenhum Dado Disponível</h3>
          <p className="text-gray-500 text-center mb-4">Não foi possível carregar os dados da planilha.</p>
          <button
            onClick={fetchData}
            className="theme-btn-primary px-4 py-2 rounded transition-colors"
          >
            Carregar Dados
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'evolucao':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Total de Leads</h3>
                <p className="text-2xl font-bold theme-primary">{data.overview.totalLeads || 'N/A'}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Média Diária</h3>
                <p className="text-2xl font-bold theme-primary">{data.overview.mediaDiaria?.toFixed(1) || 'N/A'}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Crescimento</h3>
                <p className="text-2xl font-bold theme-primary">+{data.overview.crescimento || 0}%</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Taxa de Qualidade</h3>
                <p className="text-2xl font-bold theme-primary">{data.overview.taxaQualidade?.toFixed(1) || 'N/A'}%</p>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Evolução de Leads</h3>
              {data.evolucaoTemporal && data.evolucaoTemporal.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={data.evolucaoTemporal}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="data" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="leads" stroke={themeColors.primary} fill={themeColors.secondary} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex justify-center items-center h-64 text-gray-500">
                  <div className="text-center">
                    <div className="text-4xl mb-2">📈</div>
                    <p>Dados de evolução temporal não disponíveis</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 'trafico':
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Fontes de Tráfego</h3>
              {data.fontesTrafico && data.fontesTrafico.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={data.fontesTrafico}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="canal" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="leads" fill={themeColors.primary} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex justify-center items-center h-64 text-gray-500">
                  <div className="text-center">
                    <div className="text-4xl mb-2">🎯</div>
                    <p>Dados de fontes de tráfego não disponíveis</p>
                  </div>
                </div>
              )}
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Distribuição por Canal</h3>
              {data.fontesTrafico && data.fontesTrafico.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={data.fontesTrafico}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ canal, percentual }) => `${canal}: ${percentual}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="leads"
                    >
                      {data.fontesTrafico.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex justify-center items-center h-64 text-gray-500">
                  <div className="text-center">
                    <div className="text-4xl mb-2">📊</div>
                    <p>Dados de distribuição por canal não disponíveis</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 'horario':
        return (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Distribuição Horária</h3>
            {data.distribuicaoHoraria && data.distribuicaoHoraria.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data.distribuicaoHoraria}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hora" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="leads" fill={themeColors.primary} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex justify-center items-center h-96 text-gray-500">
                <div className="text-center">
                  <div className="text-4xl mb-2">⏰</div>
                  <p>Dados de distribuição horária não disponíveis</p>
                </div>
              </div>
            )}
          </div>
        );

      case 'cidades':
        return (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Top Cidades</h3>
            {data.topCidades && data.topCidades.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data.topCidades}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="cidade" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="leads" fill={themeColors.primary} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex justify-center items-center h-96 text-gray-500">
                <div className="text-center">
                  <div className="text-4xl mb-2">🌍</div>
                  <p>Dados de cidades não disponíveis</p>
                </div>
              </div>
            )}
          </div>
        );

      case 'provedores':
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Top Provedores</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.topProvedores}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="provedor" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="leads" fill={themeColors.primary} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Ranking de Provedores</h3>
              <div className="space-y-2">
                {data.topProvedores.map((provedor, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span className="font-medium">{index + 1}. {provedor.provedor}</span>
                    <div className="text-right">
                      <span className="text-lg font-bold theme-primary">{provedor.leads}</span>
                      <span className="text-sm text-gray-500 ml-2">({provedor.percentual}%)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'leads':
        return (
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Lista de Leads - ({data.leads.length})</h3>
              <button
                onClick={downloadCSV}
                className="theme-btn-primary px-4 py-2 rounded"
              >
                Download CSV
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left">Nome</th>
                    <th className="px-4 py-2 text-left">Email</th>
                    <th className="px-4 py-2 text-left">Telefone</th>
                    <th className="px-4 py-2 text-left">Cidade</th>
                    <th className="px-4 py-2 text-left">Provedor</th>
                    <th className="px-4 py-2 text-left">Canal</th>
                    <th className="px-4 py-2 text-left">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {data.leads.map((lead) => (
                    <tr key={lead.id} className="border-t">
                      <td className="px-4 py-2">{lead.nome}</td>
                      <td className="px-4 py-2">{lead.email}</td>
                      <td className="px-4 py-2">{lead.telefone}</td>
                      <td className="px-4 py-2">{lead.cidade}</td>
                      <td className="px-4 py-2">{lead.provedor}</td>
                      <td className="px-4 py-2">{lead.canal}</td>
                      <td className="px-4 py-2">{lead.data}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold theme-primary">Dashboard Analítico</h1>
              <p className="text-sm text-gray-500">
                Última atualização: {data?.overview?.ultimaAtualizacao ? new Date(data.overview.ultimaAtualizacao).toLocaleString('pt-BR') : 'Carregando...'}
              </p>
              {(isLegacyMode || isFallbackMode) && (
                <p className="text-xs text-yellow-600">
                  {isLegacyMode ? '⚠️ Modo legado ativo' : '⚠️ Tema padrão ativo'}
                </p>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <div className="theme-bg-primary-light theme-primary px-3 py-1 rounded-full text-sm font-medium">
                Cliente: {clientName}
              </div>
              <div className="w-3 h-3 theme-bg-primary rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-500">Online</span>
            </div>
          </div>
        </div>
      </header>

      {/* Filtros de Data */}
      <div className="bg-gray-50 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Período:</label>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                placeholder="Data inicial"
              />
              <span className="text-gray-500">até</span>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                placeholder="Data final"
              />
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setFilters(prev => ({ ...prev, startDate: '', endDate: '' }));
                  fetchData();
                }}
                className="px-4 py-2 text-sm text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 theme-border-primary"
              >
                Limpar
              </button>
              <button
                onClick={fetchData}
                className="px-4 py-2 text-sm theme-btn-primary rounded-md focus:outline-none focus:ring-2 theme-border-primary"
              >
                Aplicar Filtro
              </button>
            </div>

            {(filters.startDate || filters.endDate) && (
              <div className="text-sm text-gray-600 theme-bg-primary-light px-3 py-1 rounded-full">
                📅 Filtro ativo: {filters.startDate || 'início'} - {filters.endDate || 'fim'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm whitespace-nowrap ${activeTab === tab.id
                  ? 'theme-border-primary theme-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">
              Dashboard Analítico {clientName} - Dados sincronizados automaticamente
            </p>
            <p className="text-sm text-gray-500">
              Versão 1.0 - Janeiro 2025
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

