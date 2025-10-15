# Multi-Domain Dashboard - Docker Setup

Este guia mostra como executar o sistema Multi-Domain Dashboard usando Docker, incluindo todas as ferramentas de administração e monitoramento.

## 🚀 Início Rápido

### Pré-requisitos

- Docker Desktop instalado e rodando
- Docker Compose disponível
- Python 3.8+ (para testes opcionais)

### Iniciar o Sistema

```bash
# Método 1: Usando o script automatizado (recomendado)
./docker_setup.sh start

# Método 2: Usando docker-compose diretamente
docker-compose up -d
```

### Verificar Status

```bash
# Ver status dos serviços
./docker_setup.sh status

# Ver logs em tempo real
./docker_setup.sh logs
```

## 🌐 URLs Disponíveis

Após iniciar o sistema, as seguintes URLs estarão disponíveis:

### Frontend
- **Dashboard Principal**: http://localhost:3000
- Interface React para visualização dos dados

### Backend APIs
- **API Principal**: http://localhost:5001/api/
- **Health Check**: http://localhost:5001/api/health
- **Endpoints do Dashboard**: http://localhost:5001/api/dashboard/

### Ferramentas de Administração
- **Dashboard de Admin**: http://localhost:5001/admin/dashboard/
- **API de Administração**: http://localhost:5001/api/admin/
- **Métricas do Sistema**: http://localhost:5001/api/admin/metrics/overview
- **Status dos Domínios**: http://localhost:5001/api/admin/domains

## 🏥 Dashboard de Administração

O dashboard de administração oferece:

### Visão Geral do Sistema
- Status de todos os domínios configurados
- Métricas de performance em tempo real
- Indicadores de saúde do sistema
- Estatísticas de cache e erros

### Monitoramento por Domínio
- Status individual de cada domínio
- Tempo de resposta
- Taxa de acerto do cache
- Contagem de erros nas últimas 24h
- Freshness dos dados

### Recursos Interativos
- Auto-refresh a cada 30 segundos
- Controles manuais de refresh
- Indicadores visuais de status
- Design responsivo

## 🔧 Comandos Úteis

### Script de Setup (docker_setup.sh)

```bash
# Iniciar sistema
./docker_setup.sh start

# Parar serviços
./docker_setup.sh stop

# Reiniciar serviços
./docker_setup.sh restart

# Reconstruir imagens
./docker_setup.sh rebuild

# Ver logs
./docker_setup.sh logs

# Verificar status
./docker_setup.sh status

# Executar testes
./docker_setup.sh test

# Limpar recursos
./docker_setup.sh clean

# Ajuda
./docker_setup.sh help
```

### Docker Compose Direto

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Ver logs
docker-compose logs -f

# Reconstruir
docker-compose build --no-cache

# Status dos serviços
docker-compose ps
```

## 🧪 Testando o Sistema

### Teste Automatizado

```bash
# Executar todos os testes
python3 test_multi_domain.py

# Testar URL específica
python3 test_multi_domain.py --url http://localhost:5001

# Testar apenas ferramentas de admin
python3 test_multi_domain.py --admin-only

# Testar domínio específico
python3 test_multi_domain.py --domain dashboard-desktop.com
```

### Teste Manual

1. **Verificar Health Check**:
   ```bash
   curl http://localhost:5001/api/health
   ```

2. **Testar Dashboard de Admin**:
   - Abrir http://localhost:5001/admin/dashboard/
   - Verificar se os domínios aparecem
   - Confirmar métricas em tempo real

3. **Testar API de Admin**:
   ```bash
   curl http://localhost:5001/api/admin/domains
   curl http://localhost:5001/api/admin/metrics/overview
   ```

4. **Testar Multi-Domínio**:
   ```bash
   # Testar domínio principal
   curl -H "Host: dashboard-desktop.com" http://localhost:5001/api/health
   
   # Testar dados do dashboard
   curl -H "Host: dashboard-desktop.com" http://localhost:5001/api/dashboard/overview
   ```

## 📊 Configuração de Domínios

O sistema usa o arquivo `backend/domains.json` para configurar múltiplos domínios:

```json
{
  "domains": {
    "dashboard-desktop.com": {
      "google_sheet_id": "1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI",
      "client_name": "Desktop",
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

### Adicionando Novos Domínios

1. Editar `backend/domains.json`
2. Adicionar nova configuração de domínio
3. Reiniciar o sistema: `./docker_setup.sh restart`

## 🔍 Monitoramento e Logs

### Logs do Sistema

```bash
# Ver todos os logs
docker-compose logs

# Logs do backend apenas
docker-compose logs backend

# Logs em tempo real
docker-compose logs -f

# Logs com timestamp
docker-compose logs -t
```

### Métricas Disponíveis

O sistema coleta automaticamente:

- **Performance**: Tempo de resposta, taxa de cache hit
- **Recursos**: Uso de CPU e memória
- **Negócio**: Contagem de requests, freshness dos dados
- **Disponibilidade**: Uptime, última requisição bem-sucedida

### Alertas

O sistema gera alertas automáticos para:

- Tempo de resposta > 3000ms
- Taxa de cache hit < 50%
- Taxa de erro > 10 erros/hora
- Uptime < 95%

## 🛠️ Troubleshooting

### Problemas Comuns

1. **Porta já em uso**:
   ```bash
   # Verificar processos usando as portas
   lsof -i :3000
   lsof -i :5001
   
   # Parar serviços conflitantes ou alterar portas no docker-compose.yml
   ```

2. **Docker não está rodando**:
   ```bash
   # Iniciar Docker Desktop
   # Ou no Linux:
   sudo systemctl start docker
   ```

3. **Erro de permissão**:
   ```bash
   # Dar permissão ao script
   chmod +x docker_setup.sh
   
   # Verificar permissões dos diretórios
   sudo chown -R $USER:$USER logs data
   ```

4. **Falha na construção da imagem**:
   ```bash
   # Limpar cache do Docker
   docker system prune -a
   
   # Reconstruir sem cache
   ./docker_setup.sh rebuild
   ```

### Verificação de Saúde

```bash
# Verificar se os containers estão rodando
docker-compose ps

# Verificar logs de erro
docker-compose logs | grep -i error

# Testar conectividade
curl -f http://localhost:5001/api/health
curl -f http://localhost:3000
```

### Reset Completo

```bash
# Parar tudo e limpar
./docker_setup.sh clean

# Reconstruir do zero
./docker_setup.sh rebuild
```

## 📈 Performance

### Otimizações Incluídas

- **Cache inteligente** por domínio
- **Coleta de métricas** em background
- **Logs estruturados** para análise
- **Health checks** automáticos
- **Graceful shutdown** dos serviços

### Monitoramento de Performance

- Dashboard de admin mostra métricas em tempo real
- API de métricas disponível em `/api/admin/metrics/overview`
- Logs detalhados para debugging
- Alertas automáticos para problemas

## 🔒 Segurança

### Configurações de Segurança

- Rate limiting configurável
- Isolamento por domínio
- Logs de auditoria
- Validação de configuração
- Headers de segurança

### Produção

Para ambiente de produção, considere:

1. Habilitar HTTPS
2. Configurar rate limiting mais restritivo
3. Implementar autenticação para admin
4. Configurar logs externos
5. Monitoramento avançado

## 📚 Documentação Adicional

- **Administração**: `docs/DOMAIN_ADMINISTRATION.md`
- **API**: Endpoints documentados no código
- **Configuração**: Exemplos em `backend/domains.json`
- **Testes**: Scripts em `backend/test_*.py`

## 🆘 Suporte

Se encontrar problemas:

1. Verificar logs: `./docker_setup.sh logs`
2. Executar testes: `./docker_setup.sh test`
3. Verificar configuração: `python3 backend/validate_domain_config.py backend/domains.json`
4. Reset completo: `./docker_setup.sh clean && ./docker_setup.sh start`

---

**Sistema Multi-Domain Dashboard com Ferramentas de Administração Completas** 🚀