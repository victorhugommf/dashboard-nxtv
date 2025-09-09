#!/bin/bash

# Dashboard Desktop - Modo Desenvolvimento com Hot Reload
# Este script inicia o ambiente de desenvolvimento com fast reload

set -e

echo "🚀 Dashboard Desktop - Modo Desenvolvimento"
echo "=========================================="

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[DEV]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Parar containers de produção se estiverem rodando
log "Parando containers de produção..."
docker compose down 2>/dev/null || true

# Iniciar ambiente de desenvolvimento
log "Iniciando ambiente de desenvolvimento..."
docker compose -f docker-compose.dev.yml up -d

# Aguardar inicialização
log "Aguardando inicialização dos serviços..."
sleep 5

# Verificar status
log "Verificando status dos serviços..."
docker compose -f docker-compose.dev.yml ps

echo ""
echo "🎉 Ambiente de desenvolvimento iniciado!"
echo "======================================="
echo ""
echo "📊 Acessos:"
echo "   🌐 Frontend (Hot Reload): http://localhost:3000"
echo "   🔧 Backend API: http://localhost:5001/api/health"
echo ""
echo "⚡ Fast Reload Ativo:"
echo "   - Edite arquivos em frontend/src/ e veja mudanças instantâneas"
echo "   - Edite arquivos em backend/ e o Flask reinicia automaticamente"
echo ""
echo "📋 Logs em tempo real:"
echo "   Frontend: docker compose -f docker-compose.dev.yml logs -f frontend-dev"
echo "   Backend:  docker compose -f docker-compose.dev.yml logs -f backend"
echo ""
echo "🛑 Para parar:"
echo "   docker compose -f docker-compose.dev.yml down"
echo ""

log "Ambiente pronto para desenvolvimento! 🚀"