# Dashboard Analítico Desktop - Pacote Completo

## 📋 Descrição
Dashboard analítico completo para o cliente Desktop com integração automática ao Google Sheets.

## 🎯 Características
- **Cliente:** Desktop
- **Planilha:** https://docs.google.com/spreadsheets/d/1Zw9ltzM3dti84UtNJgmYhkUM1DOLYw43xnQXuwkCVb8/edit?usp=drivesdk
- **Tema:** Verde/Cinza (identidade Desktop)
- **Tecnologia:** React + Flask + Python

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

### Opção 1: Desenvolvimento (Hot Reload) ⚡
```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```
**Recomendado para desenvolvimento - mudanças no código são refletidas instantaneamente!**

### Opção 2: Produção (Build Otimizado)
```bash
chmod +x scripts/prod.sh
./scripts/prod.sh
```

### Opção 3: Docker Manual
```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml up -d

# Produção
docker-compose up -d
```

### Opção 4: Instalação Automática no Sistema
```bash
chmod +x scripts/install.sh
./scripts/install.sh
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

### Variáveis de Ambiente:
```bash
GOOGLE_SHEET_ID=1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI
CLIENT_NAME=Desktop
THEME_COLOR=green
PORT=3000
```

### ⚠️ Importante - Dados Reais:
- **Sem Dados Simulados:** O dashboard trabalha exclusivamente com dados reais da planilha
- **Tratamento de Erro:** Mensagens claras quando a planilha não está acessível
- **Planilha Pública:** Certifique-se de que a planilha está configurada como pública para leitura

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

---
**Dashboard Desktop - Versão 1.0**
Data: Janeiro 2025

