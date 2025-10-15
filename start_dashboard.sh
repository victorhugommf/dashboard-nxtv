#!/bin/bash

# Script de inicialização rápida do Multi-Domain Dashboard
# Uso: ./start_dashboard.sh

echo "🚀 Iniciando Multi-Domain Dashboard..."
echo "====================================="

# Verificar se o Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker Desktop."
    exit 1
fi

# Executar setup completo
./docker_setup.sh start

echo ""
echo "🎉 Sistema iniciado com sucesso!"
echo ""
echo "📊 Acesse o dashboard de administração:"
echo "   http://localhost:5001/admin/dashboard/"
echo ""
echo "🌐 Frontend principal:"
echo "   http://localhost:3000"
echo ""
echo "🔧 Para parar o sistema:"
echo "   ./docker_setup.sh stop"
echo ""