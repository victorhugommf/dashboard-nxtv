# Guia de Instalação - Dashboard Desktop

## 📋 Visão Geral
Este guia fornece instruções detalhadas para instalar o Dashboard Analítico Desktop em diferentes ambientes.

## 🎯 Requisitos do Sistema

### Mínimos:
- **CPU:** 2 cores
- **RAM:** 4GB
- **Disco:** 10GB livres
- **OS:** Ubuntu 20.04+, CentOS 8+, macOS 10.15+

### Recomendados:
- **CPU:** 4 cores
- **RAM:** 8GB
- **Disco:** 20GB livres
- **OS:** Ubuntu 22.04 LTS

### Dependências:
- Python 3.8+
- Node.js 16+
- npm 8+
- Nginx 1.18+
- Git

## 🚀 Métodos de Instalação

### Método 1: Instalação Automática (Recomendado)

```bash
# 1. Extrair o pacote
tar -xzf desktop-dashboard-complete.tar.gz
cd desktop_dashboard_complete/

# 2. Executar instalação automática
chmod +x scripts/install.sh
sudo ./scripts/install.sh

# 3. Verificar instalação
curl http://localhost/api/health
```

### Método 2: Docker (Containerizado)

```bash
# 1. Pré-requisitos
sudo apt install docker.io docker-compose

# 2. Iniciar containers
docker-compose up -d

# 3. Verificar status
docker-compose ps
```

### Método 3: Instalação Manual

#### Backend (Flask):
```bash
cd backend/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

#### Frontend (React):
```bash
cd frontend/
npm install
npm run build
npm start
```

#### Nginx:
```bash
sudo cp nginx/desktop-dashboard.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/desktop-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## ⚙️ Configuração

### Variáveis de Ambiente:
```bash
# Backend
export GOOGLE_SHEET_ID="1Zw9ltzM3dti84UtNJgmYhkUM1DOLYw43xnQXuwkCVb8"
export CLIENT_NAME="Desktop"
export FLASK_ENV="production"
export PORT="5000"

# Frontend
export REACT_APP_API_URL="http://localhost:5000"
export REACT_APP_CLIENT_NAME="Desktop"
```

### Arquivo .env (Backend):
```env
GOOGLE_SHEET_ID=1Zw9ltzM3dti84UtNJgmYhkUM1DOLYw43xnQXuwkCVb8
CLIENT_NAME=Desktop
FLASK_ENV=production
PORT=5000
DEBUG=False
```

### Arquivo .env (Frontend):
```env
REACT_APP_API_URL=http://localhost:5000
REACT_APP_CLIENT_NAME=Desktop
REACT_APP_VERSION=1.0.0
```

## 🔧 Configuração Avançada

### SSL/HTTPS:
```bash
# Gerar certificado SSL
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/desktop-dashboard.key \
  -out /etc/ssl/certs/desktop-dashboard.crt

# Configurar Nginx para HTTPS
sudo cp nginx/desktop-dashboard-ssl.conf /etc/nginx/sites-available/
```

### Firewall:
```bash
# Ubuntu/Debian
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### Backup Automático:
```bash
# Adicionar ao crontab
0 2 * * * /opt/desktop-dashboard/scripts/backup.sh
```

## 📊 Verificação da Instalação

### Testes de Conectividade:
```bash
# API Health Check
curl http://localhost/api/health

# Frontend
curl http://localhost

# Endpoints específicos
curl http://localhost/api/dashboard/overview
curl http://localhost/api/dashboard/leads
```

### Logs:
```bash
# Backend
sudo journalctl -u desktop-dashboard-backend -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Docker
docker-compose logs -f
```

## 🔄 Manutenção

### Atualização:
```bash
# Parar serviços
sudo systemctl stop desktop-dashboard-backend
sudo systemctl stop nginx

# Atualizar código
git pull origin main

# Reinstalar dependências
cd backend && pip install -r requirements.txt
cd frontend && npm install && npm run build

# Reiniciar serviços
sudo systemctl start desktop-dashboard-backend
sudo systemctl start nginx
```

### Backup:
```bash
# Backup completo
sudo tar -czf desktop-dashboard-backup-$(date +%Y%m%d).tar.gz \
  /opt/desktop-dashboard/ \
  /etc/nginx/sites-available/desktop-dashboard \
  /etc/systemd/system/desktop-dashboard-backend.service
```

### Monitoramento:
```bash
# Status dos serviços
sudo systemctl status desktop-dashboard-backend
sudo systemctl status nginx

# Uso de recursos
htop
df -h
free -h
```

## 🆘 Solução de Problemas

### Backend não inicia:
```bash
# Verificar logs
sudo journalctl -u desktop-dashboard-backend -n 50

# Verificar dependências
cd /opt/desktop-dashboard/backend
source venv/bin/activate
pip list

# Testar manualmente
python app.py
```

### Frontend não carrega:
```bash
# Verificar build
cd /opt/desktop-dashboard/frontend
npm run build

# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx
```

### Problemas de conectividade:
```bash
# Verificar portas
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :5000

# Verificar firewall
sudo ufw status
sudo iptables -L
```

### Problemas com Google Sheets:
```bash
# Testar conectividade
curl "https://docs.google.com/spreadsheets/d/1Zw9ltzM3dti84UtNJgmYhkUM1DOLYw43xnQXuwkCVb8/export?format=csv&gid=0"

# Verificar permissões da planilha
# A planilha deve estar pública ou com permissões adequadas
```

## 📞 Suporte

### Logs Importantes:
- Backend: `/var/log/desktop-dashboard/`
- Nginx: `/var/log/nginx/`
- Sistema: `journalctl -u desktop-dashboard-backend`

### Comandos de Diagnóstico:
```bash
# Script de diagnóstico
./scripts/diagnose.sh

# Verificação completa
./scripts/health-check.sh
```

### Contato:
- Documentação: `docs/`
- Issues: Consulte README.md
- Logs: Sempre inclua logs relevantes

---
**Dashboard Desktop - Versão 1.0**
Última atualização: Janeiro 2025

