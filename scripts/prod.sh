#!/bin/bash

# Dashboard Desktop - Modo Produção
# Este script para o desenvolvimento e inicia o ambiente de produção

set -e

echo "🚀 Dashboard Desktop - Modo Produção"
echo "===================================="

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[PROD]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Parar containers de desenvolvimento
log "Parando ambiente de desenvolvimento..."
docker compose -f docker-compose.dev.yml down 2>/dev/null || true

# Reconstruir e iniciar produção
log "Reconstruindo containers de produção..."
docker compose build

log "Iniciando ambiente de produção..."
docker compose up -d

# Aguardar inicialização
log "Aguardando inicialização dos serviços..."
sleep 10

# Verificar status
log "Verificando status dos serviços..."
docker compose ps

echo ""
echo "🎉 Ambiente de produção iniciado!"
echo "================================="
echo ""
echo "📊 Acessos:"
echo "   🌐 Frontend: http://localhost:3000"
echo "   🔧 Backend API: http://localhost:5001/api/health"
echo ""
echo "📋 Logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 Para parar:"
echo "   docker compose down"
echo ""

log "Ambiente de produção pronto! 🚀"