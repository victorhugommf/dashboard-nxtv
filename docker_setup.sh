#!/bin/bash

# Multi-Domain Dashboard - Docker Setup Script
# Script para configurar e executar o ambiente Docker

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função para verificar se o Docker está rodando
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker não está rodando. Por favor, inicie o Docker Desktop."
        exit 1
    fi
    print_success "Docker está rodando"
}

# Função para verificar se o docker-compose está disponível
check_docker_compose() {
    if command -v docker-compose > /dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version > /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        print_error "docker-compose não encontrado. Por favor, instale o Docker Compose."
        exit 1
    fi
    print_success "Docker Compose disponível: $COMPOSE_CMD"
}

# Função para criar diretórios necessários
create_directories() {
    print_status "Criando diretórios necessários..."
    
    directories=("logs" "data" "backend/logs" "backend/data")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Criado diretório: $dir"
        fi
    done
    
    print_success "Diretórios criados"
}

# Função para validar configuração
validate_config() {
    print_status "Validando configuração..."
    
    if [ ! -f "backend/domains.json" ]; then
        print_error "Arquivo backend/domains.json não encontrado"
        exit 1
    fi
    
    # Validar JSON
    if ! python3 -m json.tool backend/domains.json > /dev/null 2>&1; then
        print_error "Arquivo domains.json contém JSON inválido"
        exit 1
    fi
    
    print_success "Configuração válida"
}

# Função para construir imagens
build_images() {
    print_status "Construindo imagens Docker..."
    
    $COMPOSE_CMD build --no-cache
    
    if [ $? -eq 0 ]; then
        print_success "Imagens construídas com sucesso"
    else
        print_error "Falha na construção das imagens"
        exit 1
    fi
}

# Função para iniciar serviços
start_services() {
    print_status "Iniciando serviços..."
    
    $COMPOSE_CMD up -d
    
    if [ $? -eq 0 ]; then
        print_success "Serviços iniciados"
    else
        print_error "Falha ao iniciar serviços"
        exit 1
    fi
}

# Função para verificar saúde dos serviços
check_health() {
    print_status "Verificando saúde dos serviços..."
    
    # Aguardar um pouco para os serviços iniciarem
    sleep 10
    
    # Verificar backend
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:5001/api/health > /dev/null 2>&1; then
            print_success "Backend está saudável"
            break
        else
            print_status "Aguardando backend... (tentativa $attempt/$max_attempts)"
            sleep 2
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "Backend não respondeu após $max_attempts tentativas"
        print_status "Verificando logs do backend..."
        $COMPOSE_CMD logs backend
        return 1
    fi
    
    # Verificar frontend
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend está saudável"
    else
        print_warning "Frontend pode não estar respondendo ainda"
    fi
    
    return 0
}

# Função para executar testes
run_tests() {
    print_status "Executando testes do sistema..."
    
    if [ -f "test_multi_domain.py" ]; then
        python3 test_multi_domain.py --url http://localhost:5001
        
        if [ $? -eq 0 ]; then
            print_success "Todos os testes passaram"
        else
            print_warning "Alguns testes falharam, mas o sistema pode estar funcionando"
        fi
    else
        print_warning "Script de teste não encontrado, pulando testes"
    fi
}

# Função para mostrar informações do sistema
show_info() {
    echo ""
    echo "🚀 MULTI-DOMAIN DASHBOARD - SISTEMA INICIADO"
    echo "=============================================="
    echo ""
    echo "📊 URLs Disponíveis:"
    echo "   Frontend:           http://localhost:3000"
    echo "   Backend API:        http://localhost:5001/api/"
    echo "   Admin Dashboard:    http://localhost:5001/admin/dashboard/"
    echo "   Admin API:          http://localhost:5001/api/admin/"
    echo "   Health Check:       http://localhost:5001/api/health"
    echo ""
    echo "🔧 Comandos Úteis:"
    echo "   Ver logs:           $COMPOSE_CMD logs -f"
    echo "   Parar serviços:     $COMPOSE_CMD down"
    echo "   Reiniciar:          $COMPOSE_CMD restart"
    echo "   Status:             $COMPOSE_CMD ps"
    echo ""
    echo "🏥 Ferramentas de Administração:"
    echo "   Dashboard Web:      http://localhost:5001/admin/dashboard/"
    echo "   API de Admin:       http://localhost:5001/api/admin/domains"
    echo "   Métricas:           http://localhost:5001/api/admin/metrics/overview"
    echo ""
    echo "📋 Domínios Configurados:"
    
    # Listar domínios do arquivo de configuração
    if command -v jq > /dev/null 2>&1; then
        jq -r '.domains | keys[]' backend/domains.json 2>/dev/null | while read domain; do
            echo "   - $domain"
        done
    else
        echo "   (instale 'jq' para ver lista de domínios)"
    fi
    
    echo ""
    echo "✅ Sistema pronto para uso!"
    echo "=============================================="
}

# Função para limpeza
cleanup() {
    print_status "Limpando recursos..."
    $COMPOSE_CMD down --volumes --remove-orphans
    docker system prune -f
    print_success "Limpeza concluída"
}

# Função principal
main() {
    echo "🚀 Multi-Domain Dashboard - Docker Setup"
    echo "========================================"
    
    case "${1:-start}" in
        "start")
            check_docker
            check_docker_compose
            create_directories
            validate_config
            build_images
            start_services
            
            if check_health; then
                run_tests
                show_info
            else
                print_error "Falha na verificação de saúde dos serviços"
                print_status "Verificando logs..."
                $COMPOSE_CMD logs
                exit 1
            fi
            ;;
            
        "stop")
            print_status "Parando serviços..."
            $COMPOSE_CMD down
            print_success "Serviços parados"
            ;;
            
        "restart")
            print_status "Reiniciando serviços..."
            $COMPOSE_CMD restart
            check_health
            print_success "Serviços reiniciados"
            ;;
            
        "rebuild")
            print_status "Reconstruindo e reiniciando..."
            $COMPOSE_CMD down
            build_images
            start_services
            check_health
            show_info
            ;;
            
        "logs")
            $COMPOSE_CMD logs -f
            ;;
            
        "status")
            $COMPOSE_CMD ps
            ;;
            
        "test")
            if [ -f "test_multi_domain.py" ]; then
                python3 test_multi_domain.py --url http://localhost:5001
            else
                print_error "Script de teste não encontrado"
                exit 1
            fi
            ;;
            
        "clean")
            cleanup
            ;;
            
        "help"|"-h"|"--help")
            echo "Uso: $0 [comando]"
            echo ""
            echo "Comandos disponíveis:"
            echo "  start     - Iniciar sistema (padrão)"
            echo "  stop      - Parar serviços"
            echo "  restart   - Reiniciar serviços"
            echo "  rebuild   - Reconstruir imagens e reiniciar"
            echo "  logs      - Ver logs em tempo real"
            echo "  status    - Ver status dos serviços"
            echo "  test      - Executar testes do sistema"
            echo "  clean     - Limpar recursos Docker"
            echo "  help      - Mostrar esta ajuda"
            ;;
            
        *)
            print_error "Comando desconhecido: $1"
            echo "Use '$0 help' para ver comandos disponíveis"
            exit 1
            ;;
    esac
}

# Executar função principal
main "$@"