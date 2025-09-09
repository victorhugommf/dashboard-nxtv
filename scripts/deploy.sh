#!/bin/bash

# Dashboard Desktop - Script de Deploy para Linode
# Este script automatiza o deploy do dashboard em uma instância Linode

set -e

echo "🚀 Dashboard Desktop - Deploy para Produção"
echo "==========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está executando como root
if [[ $EUID -eq 0 ]]; then
    error "Não execute este script como root. Use um usuário com sudo."
    exit 1
fi

# Verificar dependências
log "Verificando dependências..."
command -v docker >/dev/null 2>&1 || { error "Docker não encontrado. Instale o Docker primeiro."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { error "Docker Compose não encontrado."; exit 1; }

# Parar containers de desenvolvimento se estiverem rodando
log "Parando containers de desenvolvimento..."
docker compose -f docker-compose.dev.yml down 2>/dev/null || true
docker compose down 2>/dev/null || true

# Construir imagens de produção
log "Construindo imagens de produção..."
docker compose -f docker-compose.prod.yml build --no-cache

# Criar diretórios necessários
log "Criando diretórios necessários..."
mkdir -p ssl
mkdir -p logs
mkdir -p data

# Configurar SSL (Let's Encrypt)
setup_ssl() {
    log "Configurando SSL com Let's Encrypt..."
    
    # Instalar certbot se não estiver instalado
    if ! command -v certbot &> /dev/null; then
        log "Instalando Certbot..."
        sudo apt update
        sudo apt install -y certbot python3-certbot-nginx
    fi
    
    # Parar nginx temporariamente para obter certificado
    docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true
    
    # Obter certificado SSL
    read -p "Digite o domínio para o certificado SSL (ex: dashboard-desktop.com): " DOMAIN
    
    if [[ -n "$DOMAIN" ]]; then
        sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --agree-tos --no-eff-email
        
        # Copiar certificados para o diretório do projeto
        sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/
        sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/
        sudo chown $USER:$USER ssl/*.pem
        
        log "SSL configurado para $DOMAIN"
    else
        warn "Pulando configuração SSL. Usando certificados auto-assinados."
        # Criar certificados auto-assinados para desenvolvimento
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/privkey.pem \
            -out ssl/fullchain.pem \
            -subj "/C=BR/ST=SP/L=SaoPaulo/O=Desktop/CN=localhost"
    fi
}

# Configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    
    # Verificar se ufw está instalado
    if command -v ufw &> /dev/null; then
        sudo ufw allow 22/tcp
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw --force enable
        log "Firewall configurado"
    else
        warn "UFW não encontrado. Configure o firewall manualmente."
    fi
}

# Configurar SSL se solicitado
read -p "Configurar SSL com Let's Encrypt? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    setup_ssl
else
    warn "Pulando configuração SSL"
    # Criar certificados auto-assinados
    if [[ ! -f ssl/fullchain.pem ]]; then
        log "Criando certificados auto-assinados..."
        mkdir -p ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/privkey.pem \
            -out ssl/fullchain.pem \
            -subj "/C=BR/ST=SP/L=SaoPaulo/O=Desktop/CN=localhost"
    fi
fi

# Configurar firewall se solicitado
read -p "Configurar firewall? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    setup_firewall
fi

# Iniciar containers de produção
log "Iniciando containers de produção..."
docker compose -f docker-compose.prod.yml up -d

# Aguardar inicialização
log "Aguardando inicialização dos serviços..."
sleep 15

# Verificar status
log "Verificando status dos serviços..."
docker compose -f docker-compose.prod.yml ps

# Testar conectividade
log "Testando conectividade..."
sleep 5

if curl -s http://localhost/health > /dev/null; then
    log "✅ Dashboard respondendo corretamente"
else
    warn "⚠️  Dashboard pode não estar respondendo ainda"
fi

# Configurar renovação automática do SSL
setup_ssl_renewal() {
    log "Configurando renovação automática do SSL..."
    
    # Criar script de renovação
    cat > /tmp/renew-ssl.sh << 'EOF'
#!/bin/bash
certbot renew --quiet
if [[ $? -eq 0 ]]; then
    # Copiar certificados atualizados
    cp /etc/letsencrypt/live/*/fullchain.pem /path/to/dashboard/ssl/
    cp /etc/letsencrypt/live/*/privkey.pem /path/to/dashboard/ssl/
    # Reiniciar nginx
    docker compose -f /path/to/dashboard/docker-compose.prod.yml restart nginx
fi
EOF
    
    # Substituir path
    sed -i "s|/path/to/dashboard|$(pwd)|g" /tmp/renew-ssl.sh
    sudo mv /tmp/renew-ssl.sh /etc/cron.daily/renew-dashboard-ssl
    sudo chmod +x /etc/cron.daily/renew-dashboard-ssl
    
    log "Renovação automática configurada"
}

if [[ -f ssl/fullchain.pem ]] && [[ ! -f /etc/cron.daily/renew-dashboard-ssl ]]; then
    read -p "Configurar renovação automática do SSL? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_ssl_renewal
    fi
fi

# Informações finais
echo ""
echo "🎉 Deploy concluído com sucesso!"
echo "================================"
echo ""
echo "📊 Dashboard disponível em:"
echo "   🌐 HTTP: http://$(curl -s ifconfig.me || echo 'SEU_IP')"
echo "   🔒 HTTPS: https://$(curl -s ifconfig.me || echo 'SEU_IP')"
echo ""
echo "🔧 Comandos úteis:"
echo "   docker compose -f docker-compose.prod.yml ps"
echo "   docker compose -f docker-compose.prod.yml logs -f"
echo "   docker compose -f docker-compose.prod.yml restart"
echo ""
echo "📋 Logs:"
echo "   Nginx: docker compose -f docker-compose.prod.yml logs nginx"
echo "   Backend: docker compose -f docker-compose.prod.yml logs backend"
echo "   Frontend: docker compose -f docker-compose.prod.yml logs frontend"
echo ""
echo "🔄 Para atualizar:"
echo "   git pull && ./scripts/deploy.sh"
echo ""

log "Dashboard Desktop está online! 🚀"