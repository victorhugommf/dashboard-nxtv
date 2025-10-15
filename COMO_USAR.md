# 🚀 Como Usar o Multi-Domain Dashboard

## Início Rápido (1 comando)

```bash
./start_dashboard.sh
```

Este comando irá:
1. ✅ Verificar se o Docker está rodando
2. 🏗️ Construir as imagens necessárias
3. 🚀 Iniciar todos os serviços
4. 🔍 Verificar a saúde do sistema
5. 🧪 Executar testes básicos
6. 📊 Mostrar URLs disponíveis

## 📊 URLs Principais

Após iniciar o sistema:

### 🏥 **Dashboard de Administração** (NOVO!)
**http://localhost:5001/admin/dashboard/**

- Monitoramento em tempo real de todos os domínios
- Métricas de performance e saúde
- Status visual de cada domínio
- Auto-refresh a cada 30 segundos

### 🌐 **Frontend Principal**
**http://localhost:3000**

- Interface React para visualização dos dados
- Dashboard analítico por domínio

### 🔌 **APIs Disponíveis**
- **Health Check**: http://localhost:5001/api/health
- **Dashboard API**: http://localhost:5001/api/dashboard/
- **Admin API**: http://localhost:5001/api/admin/

## 🏥 Ferramentas de Administração

### Dashboard Web de Administração

Acesse **http://localhost:5001/admin/dashboard/** para ver:

#### 📊 Visão Geral do Sistema
- Total de domínios configurados
- Domínios saudáveis vs. com problemas
- Tempo médio de resposta
- Taxa de acerto do cache

#### 🌐 Status por Domínio
Cada domínio mostra:
- ✅ Status (saudável/aviso/crítico)
- ⚡ Tempo de resposta
- 💾 Taxa de cache hit
- ❌ Erros nas últimas 24h
- 📅 Última atualização

#### 🔄 Recursos Interativos
- Auto-refresh automático
- Botão de refresh manual
- Indicadores visuais de status
- Design responsivo

### API de Administração

#### Listar Todos os Domínios
```bash
curl http://localhost:5001/api/admin/domains
```

#### Métricas do Sistema
```bash
curl http://localhost:5001/api/admin/metrics/overview
```

#### Status de Domínio Específico
```bash
curl http://localhost:5001/api/admin/domains/dashboard-desktop.com/status
```

#### Validar Configuração
```bash
curl -X POST http://localhost:5001/api/admin/config/validate \
  -H "Content-Type: application/json" \
  -d '{"domains": {"test.com": {"google_sheet_id": "123", "client_name": "Test"}}}'
```

## 🧪 Testando o Sistema

### Teste Automático Completo
```bash
python3 test_multi_domain.py
```

### Teste Apenas Admin Tools
```bash
python3 test_multi_domain.py --admin-only
```

### Teste Manual Rápido
```bash
# Verificar saúde
curl http://localhost:5001/api/health

# Testar dashboard de admin
curl http://localhost:5001/admin/dashboard/api/status
```

## 🌐 Testando Multi-Domínio

O sistema suporta múltiplos domínios. Para testar:

```bash
# Domínio principal (configurado)
curl -H "Host: dashboard-desktop.com" http://localhost:5001/api/health

# Testar dados do dashboard
curl -H "Host: dashboard-desktop.com" http://localhost:5001/api/dashboard/overview
```

## 🔧 Comandos de Gerenciamento

### Parar o Sistema
```bash
./docker_setup.sh stop
```

### Ver Logs em Tempo Real
```bash
./docker_setup.sh logs
```

### Reiniciar Serviços
```bash
./docker_setup.sh restart
```

### Verificar Status
```bash
./docker_setup.sh status
```

### Reconstruir Imagens
```bash
./docker_setup.sh rebuild
```

### Limpeza Completa
```bash
./docker_setup.sh clean
```

## 📊 Monitoramento e Métricas

### Métricas Coletadas Automaticamente

O sistema coleta:
- **Performance**: Tempo de resposta, cache hit rate
- **Recursos**: CPU, memória
- **Negócio**: Número de requests, freshness dos dados
- **Disponibilidade**: Uptime, última requisição bem-sucedida

### Alertas Automáticos

Alertas são gerados para:
- ⚠️ Tempo de resposta > 3000ms
- ⚠️ Cache hit rate < 50%
- 🚨 Taxa de erro > 10/hora
- 🚨 Uptime < 95%

### Exportar Métricas

```bash
# Via API
curl http://localhost:5001/api/admin/metrics/overview

# Via CLI (dentro do container)
docker-compose exec backend flask export-metrics
```

## 🔍 Validação e Configuração

### Validar Configuração Atual
```bash
python3 backend/validate_domain_config.py backend/domains.json
```

### Validação Completa com Relatório
```bash
python3 backend/validate_domain_config.py backend/domains.json --json
```

### Adicionar Novo Domínio

1. Editar `backend/domains.json`:
```json
{
  "domains": {
    "dashboard-desktop.com": { ... },
    "novo-cliente.com": {
      "google_sheet_id": "SEU_SHEET_ID",
      "client_name": "Novo Cliente",
      "theme": {
        "primary_color": "#059669",
        "secondary_color": "#10b981",
        "accent_colors": ["#34d399"]
      },
      "cache_timeout": 300,
      "enabled": true
    }
  }
}
```

2. Reiniciar sistema:
```bash
./docker_setup.sh restart
```

## 🛠️ Troubleshooting

### Problema: Porta já em uso
```bash
# Verificar o que está usando a porta
lsof -i :5001
lsof -i :3000

# Parar processo ou alterar porta no docker-compose.yml
```

### Problema: Docker não responde
```bash
# Verificar status do Docker
docker info

# Reiniciar Docker Desktop se necessário
```

### Problema: Serviços não iniciam
```bash
# Ver logs detalhados
./docker_setup.sh logs

# Reset completo
./docker_setup.sh clean
./docker_setup.sh start
```

### Problema: Dashboard não carrega dados
```bash
# Verificar configuração
python3 backend/validate_domain_config.py backend/domains.json

# Testar API diretamente
curl http://localhost:5001/api/health
```

## 📱 Demonstração Completa

Para ver todas as funcionalidades:

1. **Iniciar sistema**: `./start_dashboard.sh`

2. **Abrir dashboard de admin**: http://localhost:5001/admin/dashboard/
   - Ver status de todos os domínios
   - Observar métricas em tempo real
   - Testar auto-refresh

3. **Testar APIs**:
   ```bash
   # API principal
   curl http://localhost:5001/api/health
   
   # Admin API
   curl http://localhost:5001/api/admin/domains
   ```

4. **Ver frontend**: http://localhost:3000
   - Dashboard analítico
   - Dados do Google Sheets

5. **Executar testes**: `python3 test_multi_domain.py`

## 🎯 Próximos Passos

Após ter o sistema rodando:

1. **Configurar seus domínios** em `backend/domains.json`
2. **Personalizar temas** para cada cliente
3. **Configurar alertas** personalizados
4. **Implementar autenticação** para produção
5. **Configurar HTTPS** para ambiente de produção

---

## 🆘 Precisa de Ajuda?

1. **Ver logs**: `./docker_setup.sh logs`
2. **Executar testes**: `./docker_setup.sh test`
3. **Reset completo**: `./docker_setup.sh clean && ./start_dashboard.sh`
4. **Validar config**: `python3 backend/validate_domain_config.py backend/domains.json`

**🎉 Aproveite seu Multi-Domain Dashboard com ferramentas de administração completas!**