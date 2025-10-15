# Multi-Domain Dashboard Deployment Guide

Este guia descreve como implantar e configurar o dashboard analítico em modo multi-domínio, permitindo que múltiplos clientes acessem seus próprios dados através de domínios específicos.

## Visão Geral

O sistema multi-domínio permite que uma única instância da aplicação sirva múltiplos clientes, onde cada domínio:
- Consome um GOOGLE_SHEET_ID diferente
- Tem configurações personalizadas (tema, cache, etc.)
- Mantém isolamento completo de dados
- Possui identidade visual própria

## Pré-requisitos

- Docker e Docker Compose instalados
- Acesso às planilhas do Google Sheets para cada cliente
- Configuração de DNS para os domínios dos clientes
- Certificados SSL (para produção)

## Configuração Inicial

### 1. Preparar Arquivo de Configuração

Copie o arquivo de exemplo e configure os domínios:

```bash
cp .env.example .env
```

Edite o arquivo `.env` conforme necessário:

```bash
# Multi-Domain Configuration
MULTI_DOMAIN_MODE=true
DOMAINS_CONFIG_PATH=./backend/domains.json

# Network Configuration
BACKEND_PORT=5001
FRONTEND_PORT=3000
```

### 2. Configurar Domínios

Edite o arquivo `backend/domains.json` para adicionar seus domínios:

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
    },
    "dashboard-cliente2.com": {
      "google_sheet_id": "SEU_GOOGLE_SHEET_ID_CLIENTE2",
      "client_name": "Cliente 2",
      "theme": {
        "primary_color": "#3b82f6",
        "secondary_color": "#60a5fa",
        "accent_colors": ["#93c5fd", "#bfdbfe", "#dbeafe"]
      },
      "cache_timeout": 600,
      "enabled": true
    }
  },
  "default_config": {
    "google_sheet_id": "GOOGLE_SHEET_ID_PADRAO",
    "client_name": "Default",
    "theme": {
      "primary_color": "#059669",
      "secondary_color": "#10b981",
      "accent_colors": ["#34d399", "#6ee7b7", "#a7f3d0"]
    },
    "cache_timeout": 300,
    "enabled": true
  }
}
```

## Implantação

### Desenvolvimento

Para ambiente de desenvolvimento com hot reload:

```bash
# Iniciar em modo desenvolvimento
docker-compose -f docker-compose.dev.yml up -d

# Verificar logs
docker-compose -f docker-compose.dev.yml logs -f

# Verificar saúde dos serviços
docker-compose -f docker-compose.dev.yml ps
```

### Produção

Para ambiente de produção:

```bash
# Iniciar em modo produção
docker-compose -f docker-compose.prod.yml up -d

# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f

# Verificar saúde dos serviços
docker-compose -f docker-compose.prod.yml ps
```

### Produção Simples (sem Nginx)

Para produção simples sem proxy reverso:

```bash
# Iniciar serviços básicos
docker-compose up -d

# Verificar logs
docker-compose logs -f
```

## Verificação da Implantação

### 1. Health Checks

Verifique se todos os serviços estão saudáveis:

```bash
# Verificar status dos containers
docker-compose ps

# Verificar health check detalhado
curl http://localhost:5001/api/health

# Verificar saúde de todos os domínios
curl http://localhost:5001/api/admin/domains/health
```

### 2. Teste de Domínios

Teste cada domínio configurado:

```bash
# Testar domínio específico
curl -H "Host: dashboard-cliente1.com" http://localhost:5001/api/domain/info

# Testar dados do dashboard
curl -H "Host: dashboard-cliente1.com" http://localhost:5001/api/dashboard/overview
```

### 3. Verificar Logs

Monitore os logs para identificar problemas:

```bash
# Logs do backend
docker-compose logs backend

# Logs específicos de domínio
tail -f logs/domain.log

# Logs de erro
tail -f logs/errors.log
```

## Configuração de DNS

### Desenvolvimento Local

Para testes locais, adicione entradas no arquivo `/etc/hosts`:

```
127.0.0.1 dashboard-cliente1.com
127.0.0.1 dashboard-cliente2.com
```

### Produção

Configure registros DNS A/CNAME apontando para o servidor:

```
dashboard-cliente1.com    A    SEU_IP_SERVIDOR
dashboard-cliente2.com    A    SEU_IP_SERVIDOR
```

## Configuração SSL (Produção)

### 1. Preparar Certificados

Coloque os certificados SSL na pasta `ssl/`:

```
ssl/
├── dashboard-cliente1.com.crt
├── dashboard-cliente1.com.key
├── dashboard-cliente2.com.crt
└── dashboard-cliente2.com.key
```

### 2. Configurar Nginx

Edite `nginx/sites-enabled/dashboard.conf` para incluir configurações SSL para cada domínio.

## Monitoramento

### Health Checks Automáticos

O sistema inclui health checks automáticos que verificam:

- Conectividade básica da aplicação
- Configuração de domínios válida
- Acesso às planilhas do Google Sheets
- Status do cache por domínio
- Isolamento de dados entre domínios

### Métricas por Domínio

Acesse métricas específicas por domínio:

```bash
# Status de um domínio específico
curl http://localhost:5001/api/admin/domains/dashboard-cliente1.com/status

# Estatísticas de cache
curl http://localhost:5001/api/admin/cache/stats
```

## Solução de Problemas

### Domínio Não Encontrado

**Erro:** `Domain not configured`

**Solução:**
1. Verifique se o domínio está listado em `domains.json`
2. Confirme que `enabled: true` para o domínio
3. Reinicie o container backend após mudanças na configuração

### Erro de Acesso ao Google Sheets

**Erro:** `Google sheet not accessible`

**Solução:**
1. Verifique se o GOOGLE_SHEET_ID está correto
2. Confirme que a planilha está compartilhada publicamente
3. Teste o acesso manual à planilha

### Container Não Saudável

**Erro:** Health check failing

**Solução:**
1. Verifique logs do container: `docker-compose logs backend`
2. Execute health check manual: `docker exec container_name python3 /app/docker-healthcheck.py`
3. Verifique configuração de domínios

### Performance Lenta

**Solução:**
1. Ajuste `cache_timeout` para valores maiores
2. Monitore uso de memória dos containers
3. Considere aumentar recursos do servidor

## Adicionando Novos Domínios

### 1. Atualizar Configuração

Adicione o novo domínio em `backend/domains.json`:

```json
{
  "domains": {
    "novo-cliente.com": {
      "google_sheet_id": "NOVO_GOOGLE_SHEET_ID",
      "client_name": "Novo Cliente",
      "theme": {
        "primary_color": "#8b5cf6",
        "secondary_color": "#a78bfa",
        "accent_colors": ["#c4b5fd", "#ddd6fe", "#ede9fe"]
      },
      "cache_timeout": 300,
      "enabled": true
    }
  }
}
```

### 2. Recarregar Configuração

O sistema recarrega automaticamente, mas você pode forçar:

```bash
# Recarregar configuração sem restart
curl -X POST http://localhost:5001/api/admin/reload-config

# Ou reiniciar o container
docker-compose restart backend
```

### 3. Verificar Novo Domínio

```bash
# Testar novo domínio
curl -H "Host: novo-cliente.com" http://localhost:5001/api/domain/info

# Verificar saúde
curl http://localhost:5001/api/admin/domains/novo-cliente.com/status
```

## Backup e Restauração

### Backup

```bash
# Backup da configuração
cp backend/domains.json backup/domains_$(date +%Y%m%d_%H%M%S).json

# Backup dos dados
docker run --rm -v $(pwd)/data:/backup alpine tar czf /backup/data_backup_$(date +%Y%m%d_%H%M%S).tar.gz /backup

# Backup dos logs
tar czf logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz logs/
```

### Restauração

```bash
# Restaurar configuração
cp backup/domains_YYYYMMDD_HHMMSS.json backend/domains.json

# Reiniciar serviços
docker-compose restart
```

## Migração de Configuração Legada

Se você tem uma instalação existente em modo single-domain:

### 1. Backup da Configuração Atual

```bash
# Fazer backup das variáveis de ambiente atuais
env | grep -E "(GOOGLE_SHEET_ID|CLIENT_NAME)" > legacy_config_backup.env
```

### 2. Executar Migração

```bash
# O sistema detecta automaticamente configuração legada
# e migra para o novo formato mantendo compatibilidade
docker-compose up -d
```

### 3. Verificar Migração

```bash
# Verificar se a configuração foi migrada corretamente
curl http://localhost:5001/api/admin/domains/health
```

## Segurança

### Configurações de Segurança

O arquivo `domains.json` inclui configurações de segurança:

```json
{
  "security": {
    "additional_whitelist": [
      "localhost",
      "127.0.0.1",
      "*.localhost"
    ],
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60,
      "requests_per_hour": 1000,
      "burst_limit": 10
    },
    "require_https": true,
    "max_request_size": 1048576,
    "block_suspicious_patterns": true
  }
}
```

### Recomendações

1. **HTTPS Obrigatório:** Configure `require_https: true` em produção
2. **Rate Limiting:** Ajuste limites conforme necessário
3. **Whitelist:** Mantenha lista de domínios permitidos atualizada
4. **Logs de Auditoria:** Monitore `logs/audit.log` regularmente

## Suporte

Para problemas ou dúvidas:

1. Verifique os logs em `logs/`
2. Execute health checks manuais
3. Consulte a documentação de troubleshooting em `docs/TROUBLESHOOTING.md`
4. Verifique issues conhecidos no repositório

## Changelog

- **v1.0.0:** Implementação inicial do sistema multi-domínio
- **v1.1.0:** Adição de health checks avançados
- **v1.2.0:** Suporte a configuração dinâmica sem restart