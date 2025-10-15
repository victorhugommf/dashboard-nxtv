# Dashboard Analítico Multi-Domínio - Pacote Completo

## 📋 Descrição
Dashboard analítico multi-domínio que permite servir múltiplos clientes através de uma única instância, onde cada domínio tem suas próprias configurações, dados e identidade visual.

## 🎯 Características
- **Multi-Domínio:** Suporte a múltiplos clientes em uma única instância
- **Isolamento de Dados:** Cada domínio acessa apenas seus próprios dados
- **Temas Personalizados:** Identidade visual específica por cliente
- **Configuração Dinâmica:** Adição de novos clientes sem restart
- **Retrocompatibilidade:** Funciona com configurações existentes
- **Tecnologia:** React + Flask + Python + Docker

## 📦 Estrutura do Projeto

```
desktop_dashboard_complete/
├── frontend/           # Interface React
├── backend/           # API Flask
├── data/             # Dados e análises
├── scripts/          # Scripts de instalação
├── docs/             # Documentação
└── README.md         # Este arquivo
```

## 🚀 Instalação Rápida

### Opção 1: Script de Deploy Multi-Domínio (Recomendado) ⚡
```bash
# Deploy em desenvolvimento
./scripts/deploy-multi-domain.sh deploy dev

# Deploy em produção
./scripts/deploy-multi-domain.sh deploy prod

# Verificar status
./scripts/deploy-multi-domain.sh status
```

### Opção 2: Desenvolvimento (Hot Reload)
```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

### Opção 3: Produção (Build Otimizado)
```bash
chmod +x scripts/prod.sh
./scripts/prod.sh
```

### Opção 4: Docker Manual
```bash
# Desenvolvimento multi-domínio
docker-compose -f docker-compose.dev.yml up -d

# Produção multi-domínio
docker-compose -f docker-compose.prod.yml up -d

# Produção simples
docker-compose up -d
```

## 📊 Funcionalidades

### 6 Abas Principais:
1. **Evolução Temporal** - Tendência de leads com dados reais
2. **Fontes de Tráfego** - Análise de canais (Instagram, Facebook, etc.)
3. **Distribuição Horária** - Melhores horários de captação
4. **Top Cidades** - Localização geográfica dos leads
5. **Top Provedores** - Análise de ISPs dos usuários
6. **Lista de Leads** - Tabela completa com dados reais

### Recursos Avançados:
- ✅ **Dados 100% Reais** - Conectado diretamente à planilha Google Sheets
- ✅ **Tratamento de Erros** - Mensagens claras quando dados não estão disponíveis
- ✅ **Download CSV/Excel** - Exportação dos dados reais
- ✅ **Sincronização Automática** - Atualização em tempo real
- ✅ **Interface Responsiva** - Funciona em desktop e mobile
- ✅ **Retry Automático** - Botão para tentar carregar dados novamente

## 🔧 Configuração

### Configuração Multi-Domínio:

1. **Copie o arquivo de ambiente:**
```bash
cp .env.example .env
```

2. **Configure os domínios em `backend/domains.json`:**
```json
{
  "domains": {
    "dashboard-cliente1.com": {
      "google_sheet_id": "SEU_GOOGLE_SHEET_ID_CLIENTE1",
      "client_name": "Cliente 1",
      "theme": {
        "primary_color": "#059669",
        "secondary_color": "#10b981",
        "accent_colors": ["#34d399", "#6ee7b7", "#a7f3d0"]
      },
      "cache_timeout": 300,
      "enabled": true
    }
  }
}
```

### Variáveis de Ambiente (.env):
```bash
# Multi-Domain Configuration
MULTI_DOMAIN_MODE=true
DOMAINS_CONFIG_PATH=./backend/domains.json

# Legacy Configuration (backward compatibility)
GOOGLE_SHEET_ID=1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI
CLIENT_NAME=Desktop

# Network Configuration
BACKEND_PORT=5001
FRONTEND_PORT=3000
```

### ⚠️ Importante - Configuração Multi-Domínio:
- **Isolamento de Dados:** Cada domínio acessa apenas sua planilha específica
- **Configuração Dinâmica:** Novos domínios podem ser adicionados sem restart
- **Retrocompatibilidade:** Configurações existentes continuam funcionando
- **Planilhas Públicas:** Certifique-se de que todas as planilhas estão públicas para leitura

## ⚡ Desenvolvimento vs Produção

### 🔧 Modo Desenvolvimento (Recomendado para edição):
```bash
./scripts/dev.sh
```
- **Hot Reload:** Mudanças no código são refletidas instantaneamente
- **Fast Refresh:** React atualiza componentes sem perder estado
- **Debug Mode:** Flask reinicia automaticamente
- **Volumes:** Código local montado no container

### 🚀 Modo Produção Local:
```bash
./scripts/prod.sh
```
- **Build Otimizado:** Código minificado e otimizado
- **Nginx:** Servidor web de produção
- **Performance:** Melhor performance para usuários finais
- **Estático:** Requer rebuild para mudanças

## 🌐 Deploy na Linode

### 📤 Upload Automático:
```bash
./scripts/upload-to-linode.sh
```

### 🚀 Deploy Completo:
```bash
# Na instância Linode, após upload:
cd /opt/desktop-dashboard
./scripts/deploy.sh
```

### 📋 Recursos do Deploy:
- ✅ **SSL Automático** com Let's Encrypt
- ✅ **Nginx** como proxy reverso
- ✅ **Firewall** configurado automaticamente
- ✅ **Docker** otimizado para produção
- ✅ **Backup** e renovação SSL automática
- ✅ **Monitoramento** e logs centralizados

### 📚 Documentação Completa:
- **Deploy Multi-Domínio:** `docs/MULTI_DOMAIN_DEPLOYMENT.md`
- **Deploy Linode:** `docs/DEPLOY_LINODE.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`

### Dependências:
- Python 3.8+
- Node.js 16+
- npm/yarn
- Docker (opcional)

## 📖 Documentação Completa
Consulte a pasta `docs/` para documentação detalhada.

## 🆘 Suporte
Para suporte técnico, consulte `docs/TROUBLESHOOTING.md`

## 🔄 Migração de Configuração Existente

Se você já tem uma instalação funcionando, o sistema detecta automaticamente e migra para o novo formato multi-domínio mantendo total compatibilidade.

## 🌐 Testando Localmente

Para testar múltiplos domínios localmente, adicione ao `/etc/hosts`:
```
127.0.0.1 dashboard-cliente1.com
127.0.0.1 dashboard-cliente2.com
```

## 📊 Monitoramento

### Health Checks:
```bash
# Verificar saúde geral
curl http://localhost:5001/api/health

# Verificar todos os domínios
curl http://localhost:5001/api/admin/domains/health

# Verificar domínio específico
curl -H "Host: dashboard-cliente1.com" http://localhost:5001/api/domain/info
```

---
**Dashboard Multi-Domínio - Versão 2.0**
Data: Janeiro 2025

