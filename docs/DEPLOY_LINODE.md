# 🚀 Deploy na Linode - Dashboard Desktop

Este guia detalha como fazer o deploy do Dashboard Desktop em uma instância Linode.

## 📋 Pré-requisitos

### 1. Instância Linode
- **OS:** Ubuntu 22.04 LTS (recomendado)
- **Plano:** Nanode 1GB (mínimo) ou Linode 2GB (recomendado)
- **Região:** Escolha a mais próxima dos usuários

### 2. Domínio (Opcional)
- Domínio próprio apontando para o IP da Linode
- Configuração DNS A record: `dashboard-desktop.com` → `IP_DA_LINODE`

## 🛠️ Instalação Passo a Passo

### 1. Conectar na Instância Linode

```bash
ssh root@SEU_IP_LINODE
```

### 2. Atualizar Sistema e Instalar Dependências

```bash
# Atualizar sistema
apt update && apt upgrade -y

# Instalar dependências básicas
apt install -y curl wget git unzip software-properties-common

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker --version
docker-compose --version
```

### 3. Criar Usuário para Deploy

```bash
# Criar usuário
adduser dashboard
usermod -aG sudo dashboard
usermod -aG docker dashboard

# Trocar para o usuário
su - dashboard
```

### 4. Clonar o Projeto

```bash
# Clonar repositório (substitua pela URL do seu repo)
git clone https://github.com/SEU_USUARIO/desktop-dashboard.git
cd desktop-dashboard

# Ou fazer upload dos arquivos via SCP/SFTP
```

### 5. Executar Deploy Automatizado

```bash
# Tornar script executável
chmod +x scripts/deploy.sh

# Executar deploy
./scripts/deploy.sh
```

O script irá:
- ✅ Verificar dependências
- ✅ Construir imagens Docker
- ✅ Configurar SSL (Let's Encrypt)
- ✅ Configurar firewall
- ✅ Iniciar containers
- ✅ Testar conectividade

## 🔒 Configuração SSL

### Opção 1: Let's Encrypt (Recomendado)
```bash
# Durante o deploy, escolha "y" para SSL
# Digite seu domínio quando solicitado
# Exemplo: dashboard-desktop.com
```

### Opção 2: Certificado Auto-assinado
```bash
# Durante o deploy, escolha "n" para SSL
# Será criado um certificado auto-assinado
```

## 🌐 Configuração de Domínio

### 1. DNS Records
Configure no seu provedor de DNS:
```
Type: A
Name: @
Value: IP_DA_LINODE
TTL: 300

Type: A  
Name: www
Value: IP_DA_LINODE
TTL: 300
```

### 2. Atualizar Nginx
Edite o arquivo de configuração:
```bash
nano nginx/sites-enabled/dashboard.conf
```

Substitua `dashboard-desktop.com` pelo seu domínio.

## 🔧 Comandos Úteis

### Gerenciar Containers
```bash
# Ver status
docker compose -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.prod.yml logs -f

# Reiniciar serviços
docker compose -f docker-compose.prod.yml restart

# Parar tudo
docker compose -f docker-compose.prod.yml down

# Atualizar e reiniciar
git pull && docker compose -f docker-compose.prod.yml up -d --build
```

### Monitoramento
```bash
# Uso de recursos
docker stats

# Logs do sistema
journalctl -f

# Espaço em disco
df -h

# Processos
htop
```

### Backup
```bash
# Backup dos dados
tar -czf backup-$(date +%Y%m%d).tar.gz data/ ssl/ logs/

# Backup do banco (se houver)
# docker exec container_name mysqldump -u user -p database > backup.sql
```

## 🔄 Atualizações

### Deploy de Nova Versão
```bash
# 1. Fazer backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/ ssl/

# 2. Atualizar código
git pull

# 3. Reconstruir e reiniciar
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verificar
docker compose -f docker-compose.prod.yml ps
```

### Rollback
```bash
# Voltar para commit anterior
git reset --hard HEAD~1

# Reconstruir
docker compose -f docker-compose.prod.yml up -d --build
```

## 📊 Monitoramento e Logs

### Logs Importantes
```bash
# Logs do Nginx
docker compose -f docker-compose.prod.yml logs nginx

# Logs do Backend
docker compose -f docker-compose.prod.yml logs backend

# Logs do Frontend
docker compose -f docker-compose.prod.yml logs frontend

# Logs do sistema
tail -f /var/log/syslog
```

### Métricas
```bash
# Uso de CPU e Memória
docker stats --no-stream

# Espaço em disco
du -sh data/ logs/ ssl/

# Conexões ativas
netstat -an | grep :80 | wc -l
```

## 🛡️ Segurança

### Firewall
```bash
# Verificar status
sudo ufw status

# Permitir apenas portas necessárias
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Atualizações de Segurança
```bash
# Atualizar sistema regularmente
sudo apt update && sudo apt upgrade -y

# Atualizar containers
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Backup Automático
```bash
# Criar script de backup
cat > /home/dashboard/backup.sh << 'EOF'
#!/bin/bash
cd /home/dashboard/desktop-dashboard
tar -czf /home/dashboard/backups/backup-$(date +%Y%m%d-%H%M).tar.gz data/ ssl/ logs/
find /home/dashboard/backups/ -name "backup-*.tar.gz" -mtime +7 -delete
EOF

# Tornar executável
chmod +x /home/dashboard/backup.sh

# Adicionar ao cron (backup diário às 2h)
echo "0 2 * * * /home/dashboard/backup.sh" | crontab -
```

## 🆘 Troubleshooting

### Container não inicia
```bash
# Ver logs detalhados
docker compose -f docker-compose.prod.yml logs container_name

# Verificar recursos
free -h
df -h
```

### SSL não funciona
```bash
# Verificar certificados
ls -la ssl/
openssl x509 -in ssl/fullchain.pem -text -noout

# Renovar certificado
sudo certbot renew
```

### Performance lenta
```bash
# Verificar recursos
htop
iotop

# Otimizar containers
docker system prune -f
```

## 📞 Suporte

Para problemas específicos:
1. Verificar logs dos containers
2. Verificar recursos do sistema
3. Consultar documentação do Docker
4. Verificar configuração do Nginx

---

**Dashboard Desktop na Linode - Versão 1.0**
Deploy automatizado e otimizado para produção.