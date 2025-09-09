#!/bin/bash

# Dashboard Desktop - Upload para Linode
# Script para fazer upload do projeto para uma instância Linode

set -e

echo "📤 Upload para Linode - Dashboard Desktop"
echo "========================================"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[UPLOAD]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se rsync está instalado
if ! command -v rsync &> /dev/null; then
    error "rsync não encontrado. Instale com: brew install rsync (macOS) ou apt install rsync (Linux)"
    exit 1
fi

# Solicitar informações da Linode
read -p "Digite o IP da sua instância Linode: " LINODE_IP
read -p "Digite o usuário SSH (padrão: root): " SSH_USER
SSH_USER=${SSH_USER:-root}

# Verificar conectividade
log "Testando conexão SSH..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $SSH_USER@$LINODE_IP exit 2>/dev/null; then
    error "Não foi possível conectar via SSH. Verifique:"
    echo "  - IP da Linode: $LINODE_IP"
    echo "  - Usuário SSH: $SSH_USER"
    echo "  - Chave SSH configurada"
    exit 1
fi

log "✅ Conexão SSH estabelecida"

# Criar diretório no servidor
log "Criando diretório no servidor..."
ssh $SSH_USER@$LINODE_IP "mkdir -p /opt/desktop-dashboard"

# Arquivos a serem excluídos do upload
cat > .rsync-exclude << 'EOF'
.git/
node_modules/
.DS_Store
*.log
logs/
.env
.env.local
backend/venv/
frontend/build/
ssl/
.rsync-exclude
EOF

# Fazer upload dos arquivos
log "Fazendo upload dos arquivos..."
rsync -avz --progress --exclude-from=.rsync-exclude \
    ./ $SSH_USER@$LINODE_IP:/opt/desktop-dashboard/

# Limpar arquivo temporário
rm .rsync-exclude

# Configurar permissões
log "Configurando permissões..."
ssh $SSH_USER@$LINODE_IP << 'EOF'
cd /opt/desktop-dashboard
chmod +x scripts/*.sh
chown -R $USER:$USER .
EOF

# Instalar dependências no servidor
log "Instalando dependências no servidor..."
ssh $SSH_USER@$LINODE_IP << 'EOF'
# Atualizar sistema
apt update

# Instalar Docker se não estiver instalado
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Instalar Docker Compose se não estiver instalado
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Instalando Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Verificar instalações
docker --version
docker-compose --version || docker compose version
EOF

echo ""
echo "🎉 Upload concluído com sucesso!"
echo "==============================="
echo ""
echo "📋 Próximos passos:"
echo "1. Conectar na Linode:"
echo "   ssh $SSH_USER@$LINODE_IP"
echo ""
echo "2. Navegar para o diretório:"
echo "   cd /opt/desktop-dashboard"
echo ""
echo "3. Executar o deploy:"
echo "   ./scripts/deploy.sh"
echo ""
echo "4. Acessar o dashboard:"
echo "   http://$LINODE_IP"
echo ""
echo "📚 Documentação completa:"
echo "   cat docs/DEPLOY_LINODE.md"
echo ""

log "Pronto para deploy na Linode! 🚀"