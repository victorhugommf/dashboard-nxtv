#!/bin/bash

# Dashboard Desktop - Script de Instalação Automática
# Versão: 1.0
# Data: Janeiro 2025

set -e

echo "🚀 Dashboard Desktop - Instalação Automática"
echo "============================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar sistema operacional
log "Verificando sistema operacional..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    error "Sistema operacional não suportado: $OSTYPE"
    exit 1
fi

log "Sistema detectado: $OS"

# Verificar se está executando como root
if [[ $EUID -eq 0 ]]; then
    warn "Executando como root. Recomendado usar usuário normal."
fi

# Função para instalar dependências no Ubuntu/Debian
install_ubuntu_deps() {
    log "Instalando dependências do sistema (Ubuntu/Debian)..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx git curl
}

# Função para instalar dependências no CentOS/RHEL
install_centos_deps() {
    log "Instalando dependências do sistema (CentOS/RHEL)..."
    sudo yum update -y
    sudo yum install -y python3 python3-pip nodejs npm nginx git curl
}

# Função para instalar dependências no macOS
install_macos_deps() {
    log "Instalando dependências do sistema (macOS)..."
    if ! command -v brew &> /dev/null; then
        error "Homebrew não encontrado. Instale em: https://brew.sh"
        exit 1
    fi
    brew install python3 node nginx git curl
}

# Instalar dependências do sistema
log "Instalando dependências do sistema..."
case $OS in
    "linux")
        if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
            install_ubuntu_deps
        elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
            install_centos_deps
        else
            warn "Distribuição Linux não reconhecida. Tentando instalação Ubuntu..."
            install_ubuntu_deps
        fi
        ;;
    "macos")
        install_macos_deps
        ;;
    "windows")
        error "Windows não suportado neste script. Use WSL ou Docker."
        exit 1
        ;;
esac

# Verificar instalações
log "Verificando instalações..."
python3 --version || { error "Python3 não instalado"; exit 1; }
node --version || { error "Node.js não instalado"; exit 1; }
npm --version || { error "npm não instalado"; exit 1; }

# Criar diretório de instalação
INSTALL_DIR="/opt/desktop-dashboard"
log "Criando diretório de instalação: $INSTALL_DIR"
sudo mkdir -p $INSTALL_DIR
sudo chown $USER:$USER $INSTALL_DIR

# Copiar arquivos do projeto
log "Copiando arquivos do projeto..."
cp -r . $INSTALL_DIR/
cd $INSTALL_DIR

# Configurar backend Python
log "Configurando backend Python..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..

# Configurar frontend React
log "Configurando frontend React..."
cd frontend
npm install
npm run build
cd ..

# Criar usuário do sistema
log "Criando usuário do sistema..."
if ! id "desktop-dashboard" &>/dev/null; then
    sudo useradd -r -s /bin/false desktop-dashboard
fi

# Criar arquivos de configuração
log "Criando arquivos de configuração..."

# Systemd service para backend
sudo tee /etc/systemd/system/desktop-dashboard-backend.service > /dev/null <<EOF
[Unit]
Description=Desktop Dashboard Backend
After=network.target

[Service]
Type=simple
User=desktop-dashboard
WorkingDirectory=$INSTALL_DIR/backend
Environment=PATH=$INSTALL_DIR/backend/venv/bin
ExecStart=$INSTALL_DIR/backend/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configuração Nginx
sudo tee /etc/nginx/sites-available/desktop-dashboard > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;
    
    # Frontend
    location / {
        root $INSTALL_DIR/frontend/build;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Assets
    location /static/ {
        root $INSTALL_DIR/frontend/build;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Ativar site Nginx
sudo ln -sf /etc/nginx/sites-available/desktop-dashboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Ajustar permissões
log "Ajustando permissões..."
sudo chown -R desktop-dashboard:desktop-dashboard $INSTALL_DIR
sudo chmod +x $INSTALL_DIR/backend/app.py

# Iniciar serviços
log "Iniciando serviços..."
sudo systemctl daemon-reload
sudo systemctl enable desktop-dashboard-backend
sudo systemctl start desktop-dashboard-backend

# Testar Nginx
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# Verificar status
log "Verificando status dos serviços..."
sleep 5

if sudo systemctl is-active --quiet desktop-dashboard-backend; then
    log "✅ Backend iniciado com sucesso"
else
    error "❌ Falha ao iniciar backend"
    sudo systemctl status desktop-dashboard-backend
fi

if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx iniciado com sucesso"
else
    error "❌ Falha ao iniciar Nginx"
    sudo systemctl status nginx
fi

# Testar conectividade
log "Testando conectividade..."
sleep 2

if curl -s http://localhost/api/health > /dev/null; then
    log "✅ API respondendo corretamente"
else
    warn "⚠️  API não está respondendo"
fi

if curl -s http://localhost > /dev/null; then
    log "✅ Frontend acessível"
else
    warn "⚠️  Frontend não está acessível"
fi

# Informações finais
echo ""
echo "🎉 Instalação concluída!"
echo "========================"
echo ""
echo "📊 Dashboard Desktop está rodando em:"
echo "   🌐 Frontend: http://localhost"
echo "   🔧 API: http://localhost/api/health"
echo ""
echo "🔧 Comandos úteis:"
echo "   sudo systemctl status desktop-dashboard-backend"
echo "   sudo systemctl restart desktop-dashboard-backend"
echo "   sudo systemctl status nginx"
echo "   sudo nginx -t"
echo ""
echo "📁 Arquivos instalados em: $INSTALL_DIR"
echo "📋 Logs do backend: sudo journalctl -u desktop-dashboard-backend -f"
echo "📋 Logs do Nginx: sudo tail -f /var/log/nginx/error.log"
echo ""
echo "🆘 Para suporte, consulte a documentação em docs/"
echo ""

log "Instalação finalizada com sucesso! 🚀"

