#!/bin/bash

# Dashboard Desktop - Script de Monitoramento
# Monitora a saúde do dashboard em produção

echo "📊 Dashboard Desktop - Monitoramento"
echo "==================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

check_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar containers
echo ""
echo "🐳 Status dos Containers:"
echo "------------------------"

if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    check_ok "Containers estão rodando"
    docker compose -f docker-compose.prod.yml ps
else
    check_error "Alguns containers não estão rodando"
    docker compose -f docker-compose.prod.yml ps
fi

# Verificar saúde da API
echo ""
echo "🔍 Saúde da API:"
echo "---------------"

if curl -s http://localhost/health > /dev/null; then
    API_RESPONSE=$(curl -s http://localhost/health)
    check_ok "API respondendo: $API_RESPONSE"
else
    check_error "API não está respondendo"
fi

# Verificar SSL
echo ""
echo "🔒 Status SSL:"
echo "-------------"

if [[ -f ssl/fullchain.pem ]]; then
    CERT_EXPIRY=$(openssl x509 -in ssl/fullchain.pem -noout -enddate | cut -d= -f2)
    CERT_DAYS=$(( ($(date -d "$CERT_EXPIRY" +%s) - $(date +%s)) / 86400 ))
    
    if [[ $CERT_DAYS -gt 30 ]]; then
        check_ok "Certificado SSL válido por $CERT_DAYS dias"
    elif [[ $CERT_DAYS -gt 7 ]]; then
        check_warn "Certificado SSL expira em $CERT_DAYS dias"
    else
        check_error "Certificado SSL expira em $CERT_DAYS dias - RENOVAR URGENTE!"
    fi
else
    check_warn "Certificado SSL não encontrado"
fi

# Verificar uso de recursos
echo ""
echo "💻 Uso de Recursos:"
echo "------------------"

# CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
if (( $(echo "$CPU_USAGE < 80" | bc -l) )); then
    check_ok "CPU: ${CPU_USAGE}%"
else
    check_warn "CPU: ${CPU_USAGE}% (alto)"
fi

# Memória
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
if (( $(echo "$MEM_USAGE < 80" | bc -l) )); then
    check_ok "Memória: ${MEM_USAGE}%"
else
    check_warn "Memória: ${MEM_USAGE}% (alta)"
fi

# Disco
DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | cut -d'%' -f1)
if [[ $DISK_USAGE -lt 80 ]]; then
    check_ok "Disco: ${DISK_USAGE}%"
else
    check_warn "Disco: ${DISK_USAGE}% (alto)"
fi

# Verificar logs de erro
echo ""
echo "📋 Logs Recentes:"
echo "----------------"

ERROR_COUNT=$(docker compose -f docker-compose.prod.yml logs --since="1h" 2>/dev/null | grep -i error | wc -l)
if [[ $ERROR_COUNT -eq 0 ]]; then
    check_ok "Nenhum erro na última hora"
else
    check_warn "$ERROR_COUNT erros na última hora"
    echo "Últimos erros:"
    docker compose -f docker-compose.prod.yml logs --since="1h" 2>/dev/null | grep -i error | tail -5
fi

# Verificar conectividade externa
echo ""
echo "🌐 Conectividade:"
echo "----------------"

if curl -s https://docs.google.com/spreadsheets/d/1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI/export?format=csv&gid=0 > /dev/null; then
    check_ok "Conexão com Google Sheets OK"
else
    check_error "Falha na conexão com Google Sheets"
fi

# Verificar portas
echo ""
echo "🔌 Portas:"
echo "---------"

if netstat -tuln | grep -q ":80 "; then
    check_ok "Porta 80 (HTTP) aberta"
else
    check_error "Porta 80 (HTTP) não está aberta"
fi

if netstat -tuln | grep -q ":443 "; then
    check_ok "Porta 443 (HTTPS) aberta"
else
    check_warn "Porta 443 (HTTPS) não está aberta"
fi

# Resumo
echo ""
echo "📈 Resumo do Sistema:"
echo "-------------------"
echo "Uptime: $(uptime -p)"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
echo "Containers ativos: $(docker ps | grep -c desktop-dashboard)"
echo "Espaço livre: $(df -h / | awk 'NR==2{print $4}')"

echo ""
echo "🔄 Para logs detalhados:"
echo "docker compose -f docker-compose.prod.yml logs -f"