#!/bin/bash

# Dashboard Desktop - Inicialização Rápida
# Para desenvolvimento e testes locais

set -e

echo "🚀 Dashboard Desktop - Inicialização Rápida"
echo "==========================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Verificar se está no diretório correto
if [[ ! -f "README.md" ]]; then
    echo "❌ Execute este script no diretório raiz do projeto"
    exit 1
fi

# Verificar dependências
log "Verificando dependências..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 não encontrado"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js não encontrado"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm não encontrado"; exit 1; }

# Configurar backend
log "Configurando backend..."
cd backend

if [[ ! -d "venv" ]]; then
    log "Criando ambiente virtual Python..."
    python3 -m venv venv
fi

log "Ativando ambiente virtual..."
source venv/bin/activate

log "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

log "Iniciando backend em background..."
nohup python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid

cd ..

# Configurar frontend
log "Configurando frontend..."
cd frontend

if [[ ! -d "node_modules" ]]; then
    log "Instalando dependências Node.js..."
    npm install
fi

log "Iniciando frontend em background..."
nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid

cd ..

# Criar diretório de logs se não existir
mkdir -p logs

# Aguardar inicialização
log "Aguardando inicialização dos serviços..."
sleep 10

# Verificar se os serviços estão rodando
log "Verificando status dos serviços..."

# Verificar backend
if curl -s http://localhost:5000/api/health > /dev/null; then
    log "✅ Backend rodando em http://localhost:5000"
else
    warn "⚠️  Backend pode não estar respondendo ainda"
fi

# Verificar frontend
if curl -s http://localhost:3000 > /dev/null; then
    log "✅ Frontend rodando em http://localhost:3000"
else
    warn "⚠️  Frontend pode não estar respondendo ainda"
fi

# Informações finais
echo ""
echo "🎉 Dashboard Desktop iniciado!"
echo "=============================="
echo ""
echo "📊 Acesse o dashboard em:"
echo "   🌐 Frontend: http://localhost:3000"
echo "   🔧 API: http://localhost:5000/api/health"
echo ""
echo "📋 Logs:"
echo "   Backend: tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 Para parar os serviços:"
echo "   ./scripts/stop.sh"
echo ""

# Criar script de parada
cat > scripts/stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Parando Dashboard Desktop..."

if [[ -f "logs/backend.pid" ]]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✅ Backend parado"
    fi
    rm -f logs/backend.pid
fi

if [[ -f "logs/frontend.pid" ]]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✅ Frontend parado"
    fi
    rm -f logs/frontend.pid
fi

# Matar processos Node.js e Python relacionados
pkill -f "npm start" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

echo "🎉 Dashboard Desktop parado!"
EOF

chmod +x scripts/stop.sh

log "Inicialização concluída! 🚀"

