#!/usr/bin/env python3
"""
Dashboard Desktop - API Flask
Backend para análise de dados do cliente Desktop
"""

from flask import Flask, jsonify, request, g
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import os
from io import StringIO

from domain_middleware import create_domain_middleware, get_current_config, get_current_domain, require_domain_context, get_cache_manager
from multi_domain_analyzer import MultiDomainDataAnalyzer, create_analyzer_for_domain
from domain_logger import init_domain_logging, get_domain_logger, LogCategory
from domain_security import init_domain_security, get_security_manager, SecurityConfig, RateLimitConfig
from admin_integration import setup_admin_tools, create_admin_cli_commands

app = Flask(__name__)

# Manual CORS configuration only

# Manual CORS handler for all requests
@app.before_request
def handle_cors():
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin')
        
        if origin in ['http://localhost:3000', 'http://127.0.0.1:3000']:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Domain,X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        return response

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    
    if origin in ['http://localhost:3000', 'http://127.0.0.1:3000']:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Type,Authorization'
    
    return response

# Initialize domain logging
domain_logger = init_domain_logging(app)

# Create domain middleware
middleware = create_domain_middleware(app, "domains.json")

# Setup administration tools (includes admin API, dashboard, and metrics)
admin_manager = setup_admin_tools(
    app, 
    config_file="domains.json",
    enable_metrics=True,
    enable_dashboard=True
)

# Create CLI commands for administration
create_admin_cli_commands(app)

# Initialize domain security
security_config = SecurityConfig(
    rate_limit=RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_limit=100,           # Increased for frontend compatibility
        enabled=True               # Enabled for production
    ),
    require_https=False,  # Set to True in production with SSL
    max_request_size=1024 * 1024  # 1MB
)
security_manager = init_domain_security(app, security_config)

# Legacy configurations for backward compatibility
GOOGLE_SHEET_ID = "1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI"
CLIENT_NAME = "Desktop"

class DesktopDataAnalyzer:
    def __init__(self):
        self.sheet_id = GOOGLE_SHEET_ID
        self.csv_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv&gid=0"
    
    def clean_data_for_json(self, df):
        """Remove valores NaN e prepara dados para serialização JSON"""
        # Substituir NaN por None (que se torna null no JSON)
        df_clean = df.copy()
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        return df_clean
    
    def safe_value(self, value, default=''):
        """Converte valores NaN/None para string segura"""
        if pd.isna(value) or value is None:
            return default
        
        # Converter para string
        str_value = str(value) if value != '' else default
        
        # Tentar corrigir encoding UTF-8 mal formado
        try:
            # Se for bytes, decodificar
            if isinstance(str_value, bytes):
                str_value = str_value.decode('utf-8', errors='replace')
            
            # Corrigir alguns problemas comuns de encoding
            str_value = str_value.replace('Ã¡', 'á')
            str_value = str_value.replace('Ã©', 'é') 
            str_value = str_value.replace('Ã­', 'í')
            str_value = str_value.replace('Ã³', 'ó')
            str_value = str_value.replace('Ãº', 'ú')
            str_value = str_value.replace('Ã§', 'ç')
            str_value = str_value.replace('Ã£', 'ã')
            
        except Exception:
            # Se houver erro, retornar o valor original
            pass
            
        return str_value
    
    def apply_date_filters(self, df, start_date=None, end_date=None):
        """Aplica filtros de data ao DataFrame"""
        if 'data' not in df.columns:
            return df
            
        filtered_df = df.copy()
        
        if start_date:
            try:
                start_date_parsed = pd.to_datetime(start_date).date()
                filtered_df = filtered_df[filtered_df['data'] >= start_date_parsed]
            except:
                pass  # Ignora erro de parsing de data
                
        if end_date:
            try:
                end_date_parsed = pd.to_datetime(end_date).date()
                filtered_df = filtered_df[filtered_df['data'] <= end_date_parsed]
            except:
                pass  # Ignora erro de parsing de data
                
        return filtered_df
        
    def fetch_data(self):
        """Busca dados da planilha Google Sheets"""
        try:
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()
            
            # Garantir encoding UTF-8 correto
            response.encoding = 'utf-8'
            df = pd.read_csv(StringIO(response.text), encoding='utf-8')
            return self.process_data(df)
            
        except Exception as e:
            print(f"Erro ao buscar dados da planilha: {e}")
            raise Exception(f"Não foi possível acessar a planilha do Google Sheets: {str(e)}")
    
    def process_data(self, df):
        """Processa dados da planilha"""
        try:
            # Verificar se o DataFrame não está vazio
            if df.empty:
                raise Exception("Planilha está vazia ou não contém dados válidos")
            
            # Padronizar colunas
            df.columns = df.columns.str.lower().str.strip()
            
            # Mapear colunas
            column_mapping = {
                'name': 'nome',
                'email': 'email',
                'phone': 'telefone',
                'city': 'cidade',
                'isp': 'provedor',
                'utm_medium': 'canal',
                'utm_campaign': 'campanha',
                'received_at': 'data_recebimento',
                'ip': 'ip'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            # Verificar se colunas essenciais existem
            required_columns = ['nome', 'email']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise Exception(f"Colunas obrigatórias não encontradas na planilha: {', '.join(missing_columns)}")
            
            # Processar datas
            if 'data_recebimento' in df.columns:
                df['data_recebimento'] = pd.to_datetime(df['data_recebimento'], errors='coerce')
                df['data'] = df['data_recebimento'].dt.date
                df['hora'] = df['data_recebimento'].dt.hour
            
            # Limpar dados
            df = df.dropna(subset=['nome', 'email'])
            
            if df.empty:
                raise Exception("Nenhum dado válido encontrado após processamento")
            
            return df
            
        except Exception as e:
            print(f"Erro ao processar dados da planilha: {e}")
            raise Exception(f"Erro no processamento dos dados: {str(e)}")
    


# Legacy analyzer for backward compatibility
analyzer = DesktopDataAnalyzer()

# Error handlers with domain information
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors with domain context"""
    domain_config = get_current_config()
    domain_name = get_current_domain()
    
    # Log the 404 error
    domain_logger.error(
        LogCategory.ERROR_HANDLING,
        "Resource not found (404)",
        details={
            'requested_path': request.path,
            'method': request.method,
            'user_agent': request.headers.get('User-Agent'),
            'referrer': request.headers.get('Referer')
        }
    )
    
    return jsonify({
        'error': 'Resource not found',
        'status_code': 404,
        'domain': domain_name or 'unknown',
        'client': domain_config.client_name if domain_config else 'unknown',
        'timestamp': datetime.now().isoformat(),
        'message': 'The requested resource was not found on this server'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with domain context"""
    domain_config = get_current_config()
    domain_name = get_current_domain()
    
    # Log the 500 error
    domain_logger.critical(
        LogCategory.ERROR_HANDLING,
        "Internal server error (500)",
        details={
            'error_type': type(error).__name__,
            'error_message': str(error),
            'requested_path': request.path,
            'method': request.method
        }
    )
    
    return jsonify({
        'error': 'Internal server error',
        'status_code': 500,
        'domain': domain_name or 'unknown',
        'client': domain_config.client_name if domain_config else 'unknown',
        'timestamp': datetime.now().isoformat(),
        'message': 'An internal server error occurred'
    }), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors with domain context"""
    domain_config = get_current_config()
    domain_name = get_current_domain()
    
    return jsonify({
        'error': 'Forbidden',
        'status_code': 403,
        'domain': domain_name or 'unknown',
        'client': domain_config.client_name if domain_config else 'unknown',
        'timestamp': datetime.now().isoformat(),
        'message': 'Access to this resource is forbidden'
    }), 403

@app.errorhandler(400)
def bad_request_error(error):
    """Handle 400 errors with domain context"""
    domain_config = get_current_config()
    domain_name = get_current_domain()
    
    return jsonify({
        'error': 'Bad request',
        'status_code': 400,
        'domain': domain_name or 'unknown',
        'client': domain_config.client_name if domain_config else 'unknown',
        'timestamp': datetime.now().isoformat(),
        'message': 'The request could not be understood by the server'
    }), 400

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions with domain context"""
    domain_config = get_current_config()
    domain_name = get_current_domain()
    
    # Log the full exception for debugging
    app.logger.error(f"Unhandled exception for domain {domain_name}: {str(error)}", exc_info=True)
    
    # Log with domain logger
    domain_logger.critical(
        LogCategory.ERROR_HANDLING,
        f"Unhandled exception: {str(error)}",
        details={
            'error_type': type(error).__name__,
            'requested_path': request.path,
            'method': request.method,
            'stack_trace': str(error)
        }
    )
    
    # Return a generic error response with domain information
    return jsonify({
        'error': 'Internal server error',
        'status_code': 500,
        'domain': domain_name or 'unknown',
        'client': domain_config.client_name if domain_config else 'unknown',
        'timestamp': datetime.now().isoformat(),
        'message': 'An unexpected error occurred while processing your request'
    }), 500

def get_domain_analyzer():
    """Get domain-specific analyzer or fallback to legacy analyzer"""
    domain_config = get_current_config()
    if domain_config:
        cache_manager = get_cache_manager()
        return create_analyzer_for_domain(domain_config, cache_manager)
    else:
        return analyzer

@app.route('/api/health')
@require_domain_context()
def health():
    """Endpoint de saúde"""
    domain_config = get_current_config()
    return jsonify({
        'status': 'ok',
        'client': domain_config.client_name if domain_config else CLIENT_NAME,
        'domain': domain_config.domain if domain_config else 'default',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/dashboard/overview')
@require_domain_context()
def dashboard_overview():
    """Visão geral do dashboard"""
    try:
        domain_analyzer = get_domain_analyzer()
        df = domain_analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = domain_analyzer.apply_date_filters(df, start_date, end_date)
        
        # Get client name from domain config or fallback to legacy
        domain_config = get_current_config()
        client_name = domain_config.client_name if domain_config else CLIENT_NAME
        
        overview = {
            'cliente': client_name,
            'totalLeads': len(df_filtered),
            'mediaDiaria': len(df_filtered) / max(1, df_filtered['data'].nunique()) if 'data' in df_filtered.columns else 0,
            'crescimento': 0.0,  # Calculado baseado nos dados reais
            'taxaQualidade': (df_filtered['telefone'].notna().sum() / len(df_filtered) * 100) if 'telefone' in df_filtered.columns and len(df_filtered) > 0 else 100,
            'periodo': f"{df_filtered['data'].nunique()} dias" if 'data' in df_filtered.columns else "30 dias",
            'ultimaAtualizacao': datetime.now().isoformat(),
            'filtroAtivo': bool(start_date or end_date)
        }
        
        return jsonify(overview)
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in dashboard_overview for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'dashboard_overview',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dashboard/evolucao-temporal')
@require_domain_context()
def evolucao_temporal():
    """Dados de evolução temporal"""
    try:
        domain_analyzer = get_domain_analyzer()
        df = domain_analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = domain_analyzer.apply_date_filters(df, start_date, end_date)
        
        if 'data' in df_filtered.columns:
            evolucao = df_filtered.groupby('data').size().reset_index(name='leads')
            evolucao['data'] = evolucao['data'].astype(str)
            evolucao_data = evolucao.to_dict('records')
        else:
            raise Exception("Coluna de data não encontrada nos dados da planilha")
        
        return jsonify(evolucao_data)
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in evolucao_temporal for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'evolucao_temporal',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dashboard/fontes-trafico')
@require_domain_context()
def fontes_trafico():
    """Dados de fontes de tráfego"""
    try:
        domain_analyzer = get_domain_analyzer()
        df = domain_analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = domain_analyzer.apply_date_filters(df, start_date, end_date)
        
        if 'canal' in df_filtered.columns:
            # Remover valores NaN antes de contar
            df_clean = df_filtered.dropna(subset=['canal'])
            fontes = df_clean['canal'].value_counts().head(5)
            total = len(df_clean)
            
            fontes_data = []
            for canal, leads in fontes.items():
                fontes_data.append({
                    'canal': domain_analyzer.safe_value(canal),
                    'leads': int(leads),
                    'percentual': round((leads / total) * 100, 1) if total > 0 else 0
                })
        else:
            raise Exception("Coluna de canal não encontrada nos dados da planilha")
        
        return jsonify(fontes_data)
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in fontes_trafico for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'fontes_trafico',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dashboard/distribuicao-horaria')
@require_domain_context()
def distribuicao_horaria():
    """Dados de distribuição horária"""
    try:
        domain_analyzer = get_domain_analyzer()
        df = domain_analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = domain_analyzer.apply_date_filters(df, start_date, end_date)
        
        if 'hora' in df_filtered.columns:
            horarios = df_filtered['hora'].value_counts().sort_index()
            horarios_data = []
            for hora, leads in horarios.items():
                horarios_data.append({
                    'hora': int(hora),
                    'leads': int(leads)
                })
        else:
            raise Exception("Dados de horário não disponíveis - coluna de data/hora não encontrada")
        
        return jsonify(horarios_data)
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in distribuicao_horaria for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'distribuicao_horaria',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dashboard/top-cidades')
@require_domain_context()
def top_cidades():
    """Dados de top cidades"""
    try:
        domain_analyzer = get_domain_analyzer()
        df = domain_analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = domain_analyzer.apply_date_filters(df, start_date, end_date)
        
        # Verificar qual coluna de cidade usar
        cidade_column = None
        if 'cidade-max' in df_filtered.columns:
            cidade_column = 'cidade-max'
        elif 'cidade' in df_filtered.columns:
            cidade_column = 'cidade'
        
        if cidade_column:
            total_records = len(df_filtered)
            
            # Preencher valores nulos com "Não informado"
            df_with_cidade = df_filtered.copy()
            df_with_cidade[cidade_column] = df_with_cidade[cidade_column].fillna('Não informado')
            
            # Contar todas as cidades, incluindo "Não informado"
            cidades = df_with_cidade[cidade_column].value_counts().head(10)  # Top 10 para o frontend
            
            cidades_data = []
            for cidade, leads in cidades.items():
                cidades_data.append({
                    'cidade': domain_analyzer.safe_value(cidade),
                    'leads': int(leads),
                    'percentual': round((leads / total_records) * 100, 1) if total_records > 0 else 0
                })
            
            return jsonify(cidades_data)
        else:
            raise Exception("Coluna de cidade ('cidade' ou 'cidade-max') não encontrada nos dados da planilha")
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in top_cidades for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'top_cidades',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dashboard/top-provedores')
@require_domain_context()
def top_provedores():
    """Dados de top provedores"""
    try:
        domain_analyzer = get_domain_analyzer()
        df = domain_analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = domain_analyzer.apply_date_filters(df, start_date, end_date)
        
        if 'provedor' in df_filtered.columns:
            # Remover valores NaN antes de contar
            df_clean = df_filtered.dropna(subset=['provedor'])
            provedores = df_clean['provedor'].value_counts().head(10)
            total = len(df_clean)
            
            provedores_data = []
            for provedor, leads in provedores.items():
                provedores_data.append({
                    'provedor': domain_analyzer.safe_value(provedor),
                    'leads': int(leads),
                    'percentual': round((leads / total) * 100, 1) if total > 0 else 0
                })
        else:
            raise Exception("Coluna de provedor não encontrada nos dados da planilha")
        
        return jsonify(provedores_data)
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in top_provedores for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'top_provedores',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dashboard/leads')
@require_domain_context()
def lista_leads():
    """Lista completa de leads"""
    try:
        domain_analyzer = get_domain_analyzer()
        df = domain_analyzer.fetch_data()
        
        # Filtros opcionais
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        city = request.args.get('city')
        provider = request.args.get('provider')
        
        # Aplicar filtros
        if start_date and 'data' in df.columns:
            df = df[df['data'] >= pd.to_datetime(start_date).date()]
        if end_date and 'data' in df.columns:
            df = df[df['data'] <= pd.to_datetime(end_date).date()]
        if city and 'cidade' in df.columns:
            df = df[df['cidade'] == city]
        if provider and 'provedor' in df.columns:
            df = df[df['provedor'] == provider]
        
        # Preparar dados para retorno
        leads_data = []
        for _, row in df.iterrows():
            lead = {
                'id': len(leads_data) + 1,
                'nome': domain_analyzer.safe_value(row.get('nome')),
                'email': domain_analyzer.safe_value(row.get('email')),
                'telefone': domain_analyzer.safe_value(row.get('telefone')),
                'cidade': domain_analyzer.safe_value(row.get('cidade')),
                'provedor': domain_analyzer.safe_value(row.get('provedor')),
                'canal': domain_analyzer.safe_value(row.get('canal')),
                'data': domain_analyzer.safe_value(row.get('data')) if 'data' in row else ''
            }
            leads_data.append(lead)
        
        return jsonify({
            'leads': leads_data,
            'total': len(leads_data),
            'filtros_aplicados': bool(start_date or end_date or city or provider)
        })
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in lista_leads for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'lista_leads',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dashboard/export/csv')
@require_domain_context()
def export_csv():
    """Exportar dados em CSV"""
    try:
        domain_analyzer = get_domain_analyzer()
        df = domain_analyzer.fetch_data()
        
        # Get client name for filename
        domain_config = get_current_config()
        client_name = domain_config.client_name if domain_config else CLIENT_NAME
        
        # Preparar CSV
        csv_data = df.to_csv(index=False, encoding='utf-8')
        
        return jsonify({
            'csv_data': csv_data,
            'filename': f'leads_{client_name.lower()}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in export_csv for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'export_csv',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/cache/stats')
@require_domain_context()
def cache_stats():
    """Get cache statistics for current domain"""
    try:
        domain_analyzer = get_domain_analyzer()
        
        # Get cache stats from analyzer (includes domain-specific info)
        if hasattr(domain_analyzer, 'get_cache_stats'):
            stats = domain_analyzer.get_cache_stats()
        else:
            # Fallback for legacy analyzer
            stats = {
                'cache_enabled': False,
                'message': 'Cache not available for legacy analyzer'
            }
        
        return jsonify(stats)
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in cache_stats for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'cache_stats',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/cache/invalidate', methods=['POST'])
@require_domain_context()
def invalidate_cache():
    """Invalidate cache for current domain"""
    try:
        domain_analyzer = get_domain_analyzer()
        
        # Get optional operation parameter
        operation = request.json.get('operation') if request.json else None
        
        # Invalidate cache
        if hasattr(domain_analyzer, 'invalidate_cache'):
            success = domain_analyzer.invalidate_cache(operation)
            
            if success:
                message = f"Cache invalidated successfully"
                if operation:
                    message += f" for operation: {operation}"
                
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No cache entries found to invalidate'
                })
        else:
            return jsonify({
                'success': False,
                'message': 'Cache invalidation not available for legacy analyzer'
            })
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in invalidate_cache for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'invalidate_cache',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/cache/all-stats')
@require_domain_context()
def all_cache_stats():
    """Get cache statistics for all domains (admin endpoint)"""
    try:
        cache_manager = get_cache_manager()
        
        if cache_manager:
            all_stats = cache_manager.get_all_cache_stats()
            return jsonify({
                'success': True,
                'stats': all_stats,
                'total_domains': len(all_stats)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Cache manager not available'
            })
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in all_cache_stats for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'all_cache_stats',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/domain/info')
@require_domain_context()
def domain_info():
    """Get current domain configuration information"""
    try:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        if domain_config:
            return jsonify({
                'domain': domain_name,
                'client_name': domain_config.client_name,
                'google_sheet_id': domain_config.google_sheet_id,
                'theme': {
                    'primary_color': domain_config.theme.primary_color,
                    'secondary_color': domain_config.theme.secondary_color,
                    'accent_colors': domain_config.theme.accent_colors
                },
                'cache_timeout': domain_config.cache_timeout,
                'enabled': domain_config.enabled,
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Fallback to legacy configuration
            return jsonify({
                'domain': 'legacy',
                'client_name': CLIENT_NAME,
                'google_sheet_id': GOOGLE_SHEET_ID,
                'theme': {
                    'primary_color': '#059669',
                    'secondary_color': '#10b981',
                    'accent_colors': ['#34d399', '#6ee7b7', '#a7f3d0']
                },
                'cache_timeout': 300,
                'enabled': True,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in domain_info for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'domain_info',
            'timestamp': datetime.now().isoformat()
        }), 500

# Domain Management API Endpoints

@app.route('/api/admin/domains', methods=['GET'])
def list_domains():
    """List all configured domains"""
    try:
        # Get all domains from config manager
        all_domains = []
        for domain_name in middleware.config_manager.get_all_domains():
            try:
                domain_config = middleware.config_manager.get_config_by_domain(domain_name)
                all_domains.append({
                    'domain': domain_name,
                    'client_name': domain_config.client_name,
                    'google_sheet_id': domain_config.google_sheet_id,
                    'enabled': domain_config.enabled,
                    'cache_timeout': domain_config.cache_timeout,
                    'theme': {
                        'primary_color': domain_config.theme.primary_color,
                        'secondary_color': domain_config.theme.secondary_color,
                        'accent_colors': domain_config.theme.accent_colors
                    }
                })
            except Exception as e:
                # Include domains that have configuration errors
                all_domains.append({
                    'domain': domain_name,
                    'error': str(e),
                    'enabled': False
                })
        
        return jsonify({
            'success': True,
            'domains': all_domains,
            'total_domains': len(all_domains),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.CONFIGURATION,
            f"Error listing domains: {str(e)}",
            details={'endpoint': 'list_domains'}
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'endpoint': 'list_domains',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/domains/<domain_name>', methods=['GET'])
def get_domain_config(domain_name):
    """Get configuration for a specific domain"""
    try:
        # Check if domain exists in configured domains (not fallback)
        if domain_name not in middleware.config_manager._domains:
            return jsonify({
                'success': False,
                'error': f"Domain '{domain_name}' not found",
                'domain': domain_name,
                'timestamp': datetime.now().isoformat()
            }), 404
        
        domain_config = middleware.config_manager._domains[domain_name]
        
        return jsonify({
            'success': True,
            'domain': domain_name,
            'config': {
                'client_name': domain_config.client_name,
                'google_sheet_id': domain_config.google_sheet_id,
                'enabled': domain_config.enabled,
                'cache_timeout': domain_config.cache_timeout,
                'theme': {
                    'primary_color': domain_config.theme.primary_color,
                    'secondary_color': domain_config.theme.secondary_color,
                    'accent_colors': domain_config.theme.accent_colors,
                    'logo_url': domain_config.theme.logo_url,
                    'favicon_url': domain_config.theme.favicon_url
                },
                'custom_settings': domain_config.custom_settings
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.CONFIGURATION,
            f"Error getting domain config for {domain_name}: {str(e)}",
            details={'domain': domain_name, 'endpoint': 'get_domain_config'}
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'domain': domain_name,
            'endpoint': 'get_domain_config',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/domains/<domain_name>', methods=['PUT'])
def update_domain_config(domain_name):
    """Update configuration for a specific domain"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request body must be JSON',
                'domain': domain_name,
                'timestamp': datetime.now().isoformat()
            }), 400
        
        config_data = request.get_json()
        if not config_data:
            return jsonify({
                'success': False,
                'error': 'Request body must be JSON',
                'domain': domain_name,
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Create domain config from request data
        from domain_config import DomainConfig
        domain_config = DomainConfig.from_dict(domain_name, config_data)
        
        # Validate configuration
        errors = domain_config.validate()
        if errors:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'validation_errors': errors,
                'domain': domain_name,
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Add or update domain
        middleware.config_manager.add_domain(domain_name, domain_config)
        
        domain_logger.log_configuration_change(
            "domain_updated_via_api",
            details={
                'domain': domain_name,
                'client_name': domain_config.client_name,
                'google_sheet_id': domain_config.google_sheet_id,
                'enabled': domain_config.enabled
            }
        )
        
        return jsonify({
            'success': True,
            'message': f"Domain '{domain_name}' updated successfully",
            'domain': domain_name,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.CONFIGURATION,
            f"Error updating domain config for {domain_name}: {str(e)}",
            details={'domain': domain_name, 'endpoint': 'update_domain_config'}
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'domain': domain_name,
            'endpoint': 'update_domain_config',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/domains/<domain_name>', methods=['DELETE'])
def delete_domain_config(domain_name):
    """Delete configuration for a specific domain"""
    try:
        # Check if domain exists in configured domains (not fallback)
        if domain_name not in middleware.config_manager._domains:
            return jsonify({
                'success': False,
                'error': f"Domain '{domain_name}' not found",
                'domain': domain_name,
                'timestamp': datetime.now().isoformat()
            }), 404
        
        # Remove domain
        middleware.config_manager.remove_domain(domain_name)
        
        domain_logger.log_configuration_change(
            "domain_deleted_via_api",
            details={'domain': domain_name}
        )
        
        return jsonify({
            'success': True,
            'message': f"Domain '{domain_name}' deleted successfully",
            'domain': domain_name,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.CONFIGURATION,
            f"Error deleting domain config for {domain_name}: {str(e)}",
            details={'domain': domain_name, 'endpoint': 'delete_domain_config'}
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'domain': domain_name,
            'endpoint': 'delete_domain_config',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/domains/reload', methods=['POST'])
def reload_domain_configurations():
    """Reload domain configurations without restart"""
    try:
        # Reload configurations
        middleware.config_manager.reload_configurations()
        
        # Get updated domain list
        domains = middleware.config_manager.get_all_domains()
        
        domain_logger.log_configuration_change(
            "configuration_reloaded_via_api",
            details={
                'total_domains': len(domains),
                'domains': domains
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Domain configurations reloaded successfully',
            'total_domains': len(domains),
            'domains': domains,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.CONFIGURATION,
            f"Error reloading domain configurations: {str(e)}",
            details={'endpoint': 'reload_domain_configurations'}
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'endpoint': 'reload_domain_configurations',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/domains/validate', methods=['POST'])
def validate_domain_configuration():
    """Validate domain configuration without saving"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request body must be JSON',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        config_data = request.get_json()
        if not config_data:
            return jsonify({
                'success': False,
                'error': 'Request body must be JSON',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Validate the configuration
        errors = middleware.config_manager.validate_config(config_data)
        
        if errors:
            return jsonify({
                'success': False,
                'valid': False,
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'valid': True,
                'message': 'Configuration is valid',
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.CONFIGURATION,
            f"Error validating domain configuration: {str(e)}",
            details={'endpoint': 'validate_domain_configuration'}
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'endpoint': 'validate_domain_configuration',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/domains/<domain_name>/status', methods=['GET'])
def get_domain_status(domain_name):
    """Get status and health information for a specific domain"""
    try:
        # Check if domain exists in configured domains (not fallback)
        if domain_name not in middleware.config_manager._domains:
            return jsonify({
                'success': False,
                'error': f"Domain '{domain_name}' not found",
                'domain': domain_name,
                'timestamp': datetime.now().isoformat()
            }), 404
        
        domain_config = middleware.config_manager._domains[domain_name]
        
        # Test domain health by trying to fetch data
        health_status = {
            'domain': domain_name,
            'enabled': domain_config.enabled,
            'client_name': domain_config.client_name,
            'google_sheet_accessible': False,
            'cache_status': 'unknown',
            'last_data_fetch': None,
            'error_details': None
        }
        
        if domain_config.enabled:
            try:
                # Create analyzer for this domain to test data access
                cache_manager = get_cache_manager()
                analyzer = create_analyzer_for_domain(domain_config, cache_manager)
                
                # Try to fetch data (this will test Google Sheets access)
                df = analyzer.fetch_data()
                
                health_status['google_sheet_accessible'] = True
                health_status['last_data_fetch'] = datetime.now().isoformat()
                health_status['data_rows'] = len(df) if df is not None else 0
                
                # Get cache status
                if hasattr(analyzer, 'get_cache_stats'):
                    cache_stats = analyzer.get_cache_stats()
                    health_status['cache_status'] = 'active' if cache_stats.get('cache_enabled') else 'disabled'
                    health_status['cache_hits'] = cache_stats.get('cache_hits', 0)
                    health_status['cache_misses'] = cache_stats.get('cache_misses', 0)
                
            except Exception as e:
                health_status['google_sheet_accessible'] = False
                health_status['error_details'] = str(e)
                health_status['cache_status'] = 'error'
        
        return jsonify({
            'success': True,
            'status': health_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.DOMAIN_RESOLUTION,
            f"Error getting domain status for {domain_name}: {str(e)}",
            details={'domain': domain_name, 'endpoint': 'get_domain_status'}
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'domain': domain_name,
            'endpoint': 'get_domain_status',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/domains/health', methods=['GET'])
def get_all_domains_health():
    """Get health status for all configured domains"""
    try:
        all_domains = middleware.config_manager.get_all_domains()
        health_summary = {
            'total_domains': len(all_domains),
            'healthy_domains': 0,
            'unhealthy_domains': 0,
            'disabled_domains': 0,
            'domains': []
        }
        
        for domain_name in all_domains:
            try:
                domain_config = middleware.config_manager.get_config_by_domain(domain_name)
                
                domain_health = {
                    'domain': domain_name,
                    'client_name': domain_config.client_name,
                    'enabled': domain_config.enabled,
                    'status': 'unknown'
                }
                
                if not domain_config.enabled:
                    domain_health['status'] = 'disabled'
                    health_summary['disabled_domains'] += 1
                else:
                    try:
                        # Quick health check - try to create analyzer
                        cache_manager = get_cache_manager()
                        analyzer = create_analyzer_for_domain(domain_config, cache_manager)
                        
                        # Test basic functionality without full data fetch
                        if hasattr(analyzer, 'csv_url') and analyzer.csv_url:
                            domain_health['status'] = 'healthy'
                            health_summary['healthy_domains'] += 1
                        else:
                            domain_health['status'] = 'unhealthy'
                            domain_health['error'] = 'Invalid Google Sheets configuration'
                            health_summary['unhealthy_domains'] += 1
                            
                    except Exception as e:
                        domain_health['status'] = 'unhealthy'
                        domain_health['error'] = str(e)
                        health_summary['unhealthy_domains'] += 1
                
                health_summary['domains'].append(domain_health)
                
            except Exception as e:
                health_summary['domains'].append({
                    'domain': domain_name,
                    'status': 'error',
                    'error': str(e)
                })
                health_summary['unhealthy_domains'] += 1
        
        return jsonify({
            'success': True,
            'health_summary': health_summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.CONFIGURATION,
            f"Error getting all domains health: {str(e)}",
            details={'endpoint': 'get_all_domains_health'}
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'endpoint': 'get_all_domains_health',
            'timestamp': datetime.now().isoformat()
        }), 500
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in domain_info for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'domain_info',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/theme/config')
@require_domain_context()
def theme_config():
    """Get theme configuration for current domain"""
    try:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        if domain_config:
            from theme_manager import ThemeManager
            theme_manager = ThemeManager()
            theme_data = theme_manager.get_theme_for_api(domain_config)
            
            return jsonify({
                'success': True,
                'domain': domain_name,
                'client_name': domain_config.client_name,
                **theme_data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Fallback to legacy theme configuration
            return jsonify({
                'success': True,
                'domain': 'legacy',
                'client_name': CLIENT_NAME,
                'theme': {
                    'primary_color': '#059669',
                    'secondary_color': '#10b981',
                    'accent_colors': ['#34d399', '#6ee7b7', '#a7f3d0'],
                    'logo_url': None,
                    'favicon_url': None,
                    'client_name': CLIENT_NAME,
                    'domain': 'legacy'
                },
                'branding': {
                    'client_name': CLIENT_NAME,
                    'domain': 'legacy',
                    'logo_url': None,
                    'favicon_url': None,
                    'primary_color': '#059669',
                    'secondary_color': '#10b981'
                },
                'css_variables': ':root {\n  --color-primary: #059669;\n  --color-secondary: #10b981;\n  --color-accent-1: #34d399;\n  --color-accent-2: #6ee7b7;\n  --color-accent-3: #a7f3d0;\n  --color-primary-hover: #059669dd;\n  --color-primary-active: #059669bb;\n  --color-secondary-hover: #10b981dd;\n  --color-secondary-active: #10b981bb;\n  --color-primary-bg: #0596691a;\n  --color-secondary-bg: #10b9811a;\n}',
                'legacy_mode': True,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        domain_config = get_current_config()
        domain_name = get_current_domain()
        
        # Log the error with domain context
        app.logger.error(f"Error in theme_config for domain {domain_name}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': str(e),
            'domain': domain_name or 'unknown',
            'client': domain_config.client_name if domain_config else 'unknown',
            'endpoint': 'theme_config',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/logs/domain/<domain>')
@require_domain_context()
def get_domain_logs(domain):
    """Get logs for a specific domain (admin endpoint)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        logs = domain_logger.get_domain_logs(domain, limit)
        
        return jsonify({
            'success': True,
            'domain': domain,
            'logs': logs,
            'total': len(logs)
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to retrieve logs for domain {domain}: {str(e)}"
        )
        
        return jsonify({
            'error': str(e),
            'domain': domain,
            'endpoint': 'get_domain_logs',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/logs/audit')
@require_domain_context()
def get_audit_logs():
    """Get audit trail logs (admin endpoint)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        audit_logs = domain_logger.get_audit_trail(limit)
        
        return jsonify({
            'success': True,
            'audit_logs': audit_logs,
            'total': len(audit_logs)
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to retrieve audit logs: {str(e)}"
        )
        
        return jsonify({
            'error': str(e),
            'endpoint': 'get_audit_logs',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/logs/errors')
@require_domain_context()
def get_error_summary():
    """Get error summary for monitoring (admin endpoint)"""
    try:
        domain = request.args.get('domain')
        hours = request.args.get('hours', 24, type=int)
        
        error_summary = domain_logger.get_error_summary(domain, hours)
        
        return jsonify({
            'success': True,
            'error_summary': error_summary
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to generate error summary: {str(e)}"
        )
        
        return jsonify({
            'error': str(e),
            'endpoint': 'get_error_summary',
            'timestamp': datetime.now().isoformat()
        }), 500


# Security Management API Endpoints

@app.route('/api/admin/security/stats', methods=['GET'])
@require_domain_context()
def get_security_stats():
    """Get security statistics for current domain"""
    try:
        domain = get_current_domain()
        if not domain:
            return jsonify({
                'error': 'Domain context not available',
                'endpoint': 'get_security_stats',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        security_manager = get_security_manager()
        stats = security_manager.get_security_stats(domain)
        
        domain_logger.log_api_request(
            endpoint='get_security_stats',
            domain=domain,
            success=True,
            details={'stats_retrieved': True}
        )
        
        return jsonify({
            'success': True,
            'domain': domain,
            'security_stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to get security stats: {str(e)}",
            details={'domain': domain if 'domain' in locals() else 'unknown'}
        )
        
        return jsonify({
            'error': str(e),
            'endpoint': 'get_security_stats',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/admin/security/whitelist', methods=['GET'])
@require_domain_context()
def get_domain_whitelist():
    """Get current domain whitelist"""
    try:
        security_manager = get_security_manager()
        whitelist = list(security_manager.whitelist_validator.get_whitelist())
        
        domain_logger.log_api_request(
            endpoint='get_domain_whitelist',
            success=True,
            details={'whitelist_size': len(whitelist)}
        )
        
        return jsonify({
            'success': True,
            'whitelist': whitelist,
            'count': len(whitelist),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to get domain whitelist: {str(e)}"
        )
        
        return jsonify({
            'error': str(e),
            'endpoint': 'get_domain_whitelist',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/admin/security/whitelist', methods=['POST'])
@require_domain_context()
def add_domain_to_whitelist():
    """Add domain to whitelist"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({
                'error': 'Domain is required in request body',
                'endpoint': 'add_domain_to_whitelist',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        domain_to_add = data['domain']
        security_manager = get_security_manager()
        security_manager.add_domain_to_whitelist(domain_to_add)
        
        domain_logger.log_api_request(
            endpoint='add_domain_to_whitelist',
            success=True,
            details={'added_domain': domain_to_add}
        )
        
        return jsonify({
            'success': True,
            'message': f'Domain {domain_to_add} added to whitelist',
            'domain': domain_to_add,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to add domain to whitelist: {str(e)}"
        )
        
        return jsonify({
            'error': str(e),
            'endpoint': 'add_domain_to_whitelist',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/admin/security/whitelist/<domain_name>', methods=['DELETE'])
@require_domain_context()
def remove_domain_from_whitelist(domain_name):
    """Remove domain from whitelist"""
    try:
        security_manager = get_security_manager()
        security_manager.remove_domain_from_whitelist(domain_name)
        
        domain_logger.log_api_request(
            endpoint='remove_domain_from_whitelist',
            success=True,
            details={'removed_domain': domain_name}
        )
        
        return jsonify({
            'success': True,
            'message': f'Domain {domain_name} removed from whitelist',
            'domain': domain_name,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to remove domain from whitelist: {str(e)}"
        )
        
        return jsonify({
            'error': str(e),
            'endpoint': 'remove_domain_from_whitelist',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/admin/security/rate-limit/reset', methods=['POST'])
@require_domain_context()
def reset_rate_limits():
    """Reset rate limits for current domain"""
    try:
        domain = get_current_domain()
        if not domain:
            return jsonify({
                'error': 'Domain context not available',
                'endpoint': 'reset_rate_limits',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        security_manager = get_security_manager()
        security_manager.reset_rate_limits(domain)
        
        domain_logger.log_api_request(
            endpoint='reset_rate_limits',
            domain=domain,
            success=True,
            details={'rate_limits_reset': True}
        )
        
        return jsonify({
            'success': True,
            'message': f'Rate limits reset for domain {domain}',
            'domain': domain,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to reset rate limits: {str(e)}",
            details={'domain': domain if 'domain' in locals() else 'unknown'}
        )
        
        return jsonify({
            'error': str(e),
            'endpoint': 'reset_rate_limits',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/admin/security/validate-config', methods=['POST'])
@require_domain_context()
def validate_security_config():
    """Validate security configuration"""
    try:
        security_manager = get_security_manager()
        is_valid, errors = security_manager.config_protector.validate_file_access()
        
        domain_logger.log_api_request(
            endpoint='validate_security_config',
            success=True,
            details={'config_valid': is_valid, 'error_count': len(errors)}
        )
        
        return jsonify({
            'success': True,
            'config_valid': is_valid,
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        domain_logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to validate security config: {str(e)}"
        )
        
        return jsonify({
            'error': str(e),
            'endpoint': 'validate_security_config',
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    print(f"🚀 Iniciando API Dashboard Multi-Domínio")
    print(f"📊 Configuração legada: {CLIENT_NAME} - {GOOGLE_SHEET_ID}")
    print(f"🌐 Servidor: http://localhost:5000")
    print(f"🔧 Configuração de domínios: domains.json")
    
    # Display configured domains
    try:
        from domain_config import DomainConfigManager
        config_manager = DomainConfigManager("domains.json")
        domains = config_manager.get_all_domains()
        
        if domains:
            print(f"🏢 Domínios configurados:")
            for domain in domains:
                try:
                    config = config_manager.get_config_by_domain(domain)
                    status = "✅ Ativo" if config.enabled else "❌ Inativo"
                    print(f"   • {domain} -> {config.client_name} {status}")
                except Exception as e:
                    print(f"   • {domain} -> ❌ Erro: {str(e)}")
        else:
            print(f"⚠️  Nenhum domínio configurado - usando configuração legada")
            
    except Exception as e:
        print(f"⚠️  Erro ao carregar configuração de domínios: {str(e)}")
        print(f"🔄 Continuando com configuração legada")
    
    print(f"🎯 Endpoints disponíveis:")
    print(f"   • GET  /api/health - Status do sistema")
    print(f"   • GET  /api/domain/info - Informações do domínio")
    print(f"   • GET  /api/dashboard/* - Endpoints do dashboard")
    print(f"   • GET  /api/cache/* - Gerenciamento de cache")
    print(f"")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

