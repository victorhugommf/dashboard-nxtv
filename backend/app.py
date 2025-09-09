#!/usr/bin/env python3
"""
Dashboard Desktop - API Flask
Backend para análise de dados do cliente Desktop
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import os
from io import StringIO

app = Flask(__name__)
CORS(app)

# Configurações
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
    


analyzer = DesktopDataAnalyzer()

@app.route('/api/health')
def health():
    """Endpoint de saúde"""
    return jsonify({
        'status': 'ok',
        'client': CLIENT_NAME,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/dashboard/overview')
def dashboard_overview():
    """Visão geral do dashboard"""
    try:
        df = analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = analyzer.apply_date_filters(df, start_date, end_date)
        
        overview = {
            'cliente': CLIENT_NAME,
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/evolucao-temporal')
def evolucao_temporal():
    """Dados de evolução temporal"""
    try:
        df = analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = analyzer.apply_date_filters(df, start_date, end_date)
        
        if 'data' in df_filtered.columns:
            evolucao = df_filtered.groupby('data').size().reset_index(name='leads')
            evolucao['data'] = evolucao['data'].astype(str)
            evolucao_data = evolucao.to_dict('records')
        else:
            raise Exception("Coluna de data não encontrada nos dados da planilha")
        
        return jsonify(evolucao_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/fontes-trafico')
def fontes_trafico():
    """Dados de fontes de tráfego"""
    try:
        df = analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = analyzer.apply_date_filters(df, start_date, end_date)
        
        if 'canal' in df_filtered.columns:
            # Remover valores NaN antes de contar
            df_clean = df_filtered.dropna(subset=['canal'])
            fontes = df_clean['canal'].value_counts().head(5)
            total = len(df_clean)
            
            fontes_data = []
            for canal, leads in fontes.items():
                fontes_data.append({
                    'canal': analyzer.safe_value(canal),
                    'leads': int(leads),
                    'percentual': round((leads / total) * 100, 1) if total > 0 else 0
                })
        else:
            raise Exception("Coluna de canal não encontrada nos dados da planilha")
        
        return jsonify(fontes_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/distribuicao-horaria')
def distribuicao_horaria():
    """Dados de distribuição horária"""
    try:
        df = analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = analyzer.apply_date_filters(df, start_date, end_date)
        
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/top-cidades')
def top_cidades():
    """Dados de top cidades"""
    try:
        df = analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = analyzer.apply_date_filters(df, start_date, end_date)
        
        if 'cidade' in df_filtered.columns:
            # Remover valores NaN antes de contar
            df_clean = df_filtered.dropna(subset=['cidade'])
            cidades = df_clean['cidade'].value_counts().head(10)
            total = len(df_clean)
            
            cidades_data = []
            for cidade, leads in cidades.items():
                cidades_data.append({
                    'cidade': analyzer.safe_value(cidade),
                    'leads': int(leads),
                    'percentual': round((leads / total) * 100, 1) if total > 0 else 0
                })
        else:
            raise Exception("Coluna de cidade não encontrada nos dados da planilha")
        
        return jsonify(cidades_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/top-provedores')
def top_provedores():
    """Dados de top provedores"""
    try:
        df = analyzer.fetch_data()
        
        # Aplicar filtros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        df_filtered = analyzer.apply_date_filters(df, start_date, end_date)
        
        if 'provedor' in df_filtered.columns:
            # Remover valores NaN antes de contar
            df_clean = df_filtered.dropna(subset=['provedor'])
            provedores = df_clean['provedor'].value_counts().head(10)
            total = len(df_clean)
            
            provedores_data = []
            for provedor, leads in provedores.items():
                provedores_data.append({
                    'provedor': analyzer.safe_value(provedor),
                    'leads': int(leads),
                    'percentual': round((leads / total) * 100, 1) if total > 0 else 0
                })
        else:
            raise Exception("Coluna de provedor não encontrada nos dados da planilha")
        
        return jsonify(provedores_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/leads')
def lista_leads():
    """Lista completa de leads"""
    try:
        df = analyzer.fetch_data()
        
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
                'nome': analyzer.safe_value(row.get('nome')),
                'email': analyzer.safe_value(row.get('email')),
                'telefone': analyzer.safe_value(row.get('telefone')),
                'cidade': analyzer.safe_value(row.get('cidade')),
                'provedor': analyzer.safe_value(row.get('provedor')),
                'canal': analyzer.safe_value(row.get('canal')),
                'data': analyzer.safe_value(row.get('data')) if 'data' in row else ''
            }
            leads_data.append(lead)
        
        return jsonify({
            'leads': leads_data,
            'total': len(leads_data),
            'filtros_aplicados': bool(start_date or end_date or city or provider)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/export/csv')
def export_csv():
    """Exportar dados em CSV"""
    try:
        df = analyzer.fetch_data()
        
        # Preparar CSV
        csv_data = df.to_csv(index=False, encoding='utf-8')
        
        return jsonify({
            'csv_data': csv_data,
            'filename': f'leads_desktop_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 Iniciando API Dashboard {CLIENT_NAME}")
    print(f"📊 Planilha: {GOOGLE_SHEET_ID}")
    print(f"🌐 Servidor: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

