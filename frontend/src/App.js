import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#059669', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0'];

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

      // Buscar dados de diferentes endpoints
      const [overviewRes, evolucaoRes, traficoRes, horarioRes, cidadesRes, provedoresRes, leadsRes] = await Promise.all([
        fetch(`/api/dashboard/overview${urlSuffix}`),
        fetch(`/api/dashboard/evolucao-temporal${urlSuffix}`),
        fetch(`/api/dashboard/fontes-trafico${urlSuffix}`),
        fetch(`/api/dashboard/distribuicao-horaria${urlSuffix}`),
        fetch(`/api/dashboard/top-cidades${urlSuffix}`),
        fetch(`/api/dashboard/top-provedores${urlSuffix}`),
        fetch(`/api/dashboard/leads${urlSuffix}`)
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
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
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
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
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
                <p className="text-2xl font-bold text-green-600">{data.overview.totalLeads || 'N/A'}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Média Diária</h3>
                <p className="text-2xl font-bold text-green-600">{data.overview.mediaDiaria?.toFixed(1) || 'N/A'}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Crescimento</h3>
                <p className="text-2xl font-bold text-green-600">+{data.overview.crescimento || 0}%</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Taxa de Qualidade</h3>
                <p className="text-2xl font-bold text-green-600">{data.overview.taxaQualidade?.toFixed(1) || 'N/A'}%</p>
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
                    <Area type="monotone" dataKey="leads" stroke="#059669" fill="#10b981" />
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
                    <Bar dataKey="leads" fill="#059669" />
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
                  <Bar dataKey="leads" fill="#059669" />
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
                  <Bar dataKey="leads" fill="#059669" />
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
                  <Bar dataKey="leads" fill="#059669" />
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
                      <span className="text-lg font-bold text-green-600">{provedor.leads}</span>
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
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
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
              <h1 className="text-2xl font-bold text-green-600">Dashboard Analítico</h1>
              <p className="text-sm text-gray-500">
                Última atualização: {data?.overview?.ultimaAtualizacao ? new Date(data.overview.ultimaAtualizacao).toLocaleString('pt-BR') : 'Carregando...'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                Cliente: Proxxima
              </div>
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
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
                className="px-4 py-2 text-sm text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                Limpar
              </button>
              <button
                onClick={fetchData}
                className="px-4 py-2 text-sm text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                Aplicar Filtro
              </button>
            </div>

            {(filters.startDate || filters.endDate) && (
              <div className="text-sm text-gray-600 bg-green-50 px-3 py-1 rounded-full">
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
                  ? 'border-green-500 text-green-600'
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
              Dashboard Analítico Proxxima - Dados sincronizados automaticamente
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

