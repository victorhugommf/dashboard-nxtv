#!/usr/bin/env python3
"""
Multi-Domain Data Analyzer
Extends the original DesktopDataAnalyzer to support multiple domains with complete data isolation
"""

import pandas as pd
import requests
from datetime import datetime
from io import StringIO
from typing import Optional, Dict, Any
import hashlib
import logging
import pickle

from domain_config import DomainConfig
from domain_cache import DomainCacheManager
from domain_logger import get_domain_logger, LogCategory


class MultiDomainDataAnalyzer:
    """
    Multi-domain data analyzer that provides complete data isolation between domains.
    Each domain uses its own Google Sheets ID and has isolated cache keys.
    """
    
    def __init__(self, domain_config: DomainConfig, cache_manager: Optional[DomainCacheManager] = None):
        """Initialize analyzer with domain-specific configuration"""
        self.domain_config = domain_config
        self.domain = domain_config.domain
        self.sheet_id = domain_config.google_sheet_id
        self.client_name = domain_config.client_name
        self.csv_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv&gid=0"
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(f"{__name__}.{self.domain}")
        self.domain_logger = get_domain_logger()
        
        # Log initialization for audit trail
        self.logger.info(f"Initialized MultiDomainDataAnalyzer for domain: {self.domain}, client: {self.client_name}")
        self.domain_logger.info(
            LogCategory.DATA_ACCESS,
            f"Initialized analyzer for domain: {self.domain}",
            details={
                'client_name': self.client_name,
                'google_sheet_id': self.sheet_id,
                'cache_enabled': self.cache_manager is not None
            }
        )
        
        if self.cache_manager:
            self.logger.info(f"Cache manager enabled for domain: {self.domain}")
    
    def get_cache_key(self, operation: str = "fetch_data", **kwargs) -> str:
        """
        Generate domain-aware cache key to ensure complete isolation between domains.
        
        Args:
            operation: The operation being cached (e.g., 'fetch_data', 'overview', etc.)
            **kwargs: Additional parameters to include in cache key
        
        Returns:
            Unique cache key for this domain and operation
        """
        # Create base key with domain and sheet ID for isolation
        base_key = f"domain:{self.domain}:sheet:{self.sheet_id}:op:{operation}"
        
        # Add any additional parameters to the key
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_params = sorted(kwargs.items())
            params_str = ":".join([f"{k}={v}" for k, v in sorted_params])
            base_key = f"{base_key}:params:{params_str}"
        
        # Hash the key to ensure consistent length and avoid special characters
        cache_key = hashlib.md5(base_key.encode('utf-8')).hexdigest()
        
        self.logger.debug(f"Generated cache key: {cache_key} for operation: {operation}")
        return cache_key
    
    def clean_data_for_json(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove valores NaN e prepara dados para serialização JSON"""
        # Substituir NaN por None (que se torna null no JSON)
        df_clean = df.copy()
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        return df_clean
    
    def safe_value(self, value: Any, default: str = '') -> str:
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
    
    def apply_date_filters(self, df: pd.DataFrame, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Aplica filtros de data ao DataFrame"""
        if 'data' not in df.columns:
            return df
            
        filtered_df = df.copy()
        
        if start_date:
            try:
                start_date_parsed = pd.to_datetime(start_date).date()
                filtered_df = filtered_df[filtered_df['data'] >= start_date_parsed]
                self.logger.debug(f"Applied start_date filter: {start_date}")
            except Exception as e:
                self.logger.warning(f"Failed to parse start_date {start_date}: {e}")
                
        if end_date:
            try:
                end_date_parsed = pd.to_datetime(end_date).date()
                filtered_df = filtered_df[filtered_df['data'] <= end_date_parsed]
                self.logger.debug(f"Applied end_date filter: {end_date}")
            except Exception as e:
                self.logger.warning(f"Failed to parse end_date {end_date}: {e}")
                
        return filtered_df
    
    def fetch_data(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Busca dados da planilha Google Sheets específica do domínio.
        Garante isolamento completo de dados entre domínios.
        Utiliza cache domain-aware quando disponível.
        """
        cache_key = self.get_cache_key("fetch_data")
        
        # Try to get from cache first if caching is enabled
        if use_cache and self.cache_manager:
            cached_data = self.cache_manager.get(self.domain, cache_key)
            if cached_data is not None:
                try:
                    # Deserialize cached DataFrame
                    df = pickle.loads(cached_data)
                    self.logger.info(f"Cache hit: Retrieved {len(df)} records for domain {self.domain}")
                    self.domain_logger.log_cache_operation("get", cache_key, True, {"rows": len(df)})
                    return df
                except Exception as e:
                    self.logger.warning(f"Failed to deserialize cached data for domain {self.domain}: {e}")
                    self.domain_logger.log_cache_operation("get", cache_key, False, {"error": str(e)})
                    # Continue to fetch fresh data
        
        try:
            self.logger.info(f"Fetching fresh data for domain {self.domain} from sheet {self.sheet_id}")
            self.domain_logger.log_data_access("fetch_sheet_data", True, {
                "domain": self.domain,
                "sheet_id": self.sheet_id,
                "cache_used": False
            })
            
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()
            
            # Garantir encoding UTF-8 correto
            response.encoding = 'utf-8'
            df = pd.read_csv(StringIO(response.text), encoding='utf-8')
            
            # Apply domain-specific processing
            processed_df = self.process_data(df)
            
            # Cache the processed data if cache manager is available
            if self.cache_manager:
                try:
                    # Serialize DataFrame for caching
                    serialized_data = pickle.dumps(processed_df)
                    self.cache_manager.set_with_domain_config(
                        self.domain, 
                        cache_key, 
                        serialized_data, 
                        self.domain_config
                    )
                    self.logger.debug(f"Cached data for domain {self.domain} with timeout {self.domain_config.cache_timeout}s")
                    self.domain_logger.log_cache_operation("set", cache_key, True, {
                        "rows": len(processed_df),
                        "timeout": self.domain_config.cache_timeout
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to cache data for domain {self.domain}: {e}")
                    self.domain_logger.log_cache_operation("set", cache_key, False, {"error": str(e)})
            
            self.logger.info(f"Successfully fetched {len(processed_df)} records for domain {self.domain}")
            self.domain_logger.log_data_access("process_data", True, {
                "domain": self.domain,
                "rows_processed": len(processed_df),
                "client_name": self.client_name
            })
            return processed_df
            
        except Exception as e:
            error_msg = f"Erro ao buscar dados da planilha para domínio {self.domain}: {e}"
            self.logger.error(error_msg)
            self.domain_logger.log_data_access("fetch_sheet_data", False, {
                "domain": self.domain,
                "sheet_id": self.sheet_id,
                "error": str(e)
            })
            raise Exception(f"Não foi possível acessar a planilha do Google Sheets para {self.client_name}: {str(e)}")
    
    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados da planilha com configurações específicas do domínio.
        Aplica processamento isolado por domínio.
        """
        try:
            # Verificar se o DataFrame não está vazio
            if df.empty:
                raise Exception(f"Planilha do domínio {self.domain} está vazia ou não contém dados válidos")
            
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
                raise Exception(f"Colunas obrigatórias não encontradas na planilha do domínio {self.domain}: {', '.join(missing_columns)}")
            
            # Processar datas
            if 'data_recebimento' in df.columns:
                df['data_recebimento'] = pd.to_datetime(df['data_recebimento'], errors='coerce')
                df['data'] = df['data_recebimento'].dt.date
                df['hora'] = df['data_recebimento'].dt.hour
            
            # Limpar dados
            df = df.dropna(subset=['nome', 'email'])
            
            if df.empty:
                raise Exception(f"Nenhum dado válido encontrado após processamento para domínio {self.domain}")
            
            # Apply domain-specific processing if needed
            df = self.apply_domain_specific_processing(df)
            
            self.logger.debug(f"Processed {len(df)} records for domain {self.domain}")
            return df
            
        except Exception as e:
            error_msg = f"Erro ao processar dados da planilha para domínio {self.domain}: {e}"
            self.logger.error(error_msg)
            raise Exception(f"Erro no processamento dos dados para {self.client_name}: {str(e)}")
    
    def apply_domain_specific_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica processamento específico do domínio aos dados.
        Pode ser estendido para aplicar regras de negócio específicas por cliente.
        
        Args:
            df: DataFrame com os dados processados
            
        Returns:
            DataFrame com processamento específico do domínio aplicado
        """
        # Apply any custom processing based on domain configuration
        custom_settings = self.domain_config.custom_settings
        
        # Example: Apply custom data transformations based on domain settings
        if 'data_transformations' in custom_settings:
            transformations = custom_settings['data_transformations']
            
            # Apply custom column mappings if specified
            if 'column_mappings' in transformations:
                custom_mappings = transformations['column_mappings']
                df = df.rename(columns=custom_mappings)
                self.logger.debug(f"Applied custom column mappings for domain {self.domain}")
            
            # Apply custom filters if specified
            if 'filters' in transformations:
                filters = transformations['filters']
                for filter_config in filters:
                    column = filter_config.get('column')
                    condition = filter_config.get('condition')
                    value = filter_config.get('value')
                    
                    if column in df.columns and condition and value is not None:
                        if condition == 'equals':
                            df = df[df[column] == value]
                        elif condition == 'not_equals':
                            df = df[df[column] != value]
                        elif condition == 'contains':
                            df = df[df[column].str.contains(str(value), na=False)]
                        
                        self.logger.debug(f"Applied custom filter for domain {self.domain}: {column} {condition} {value}")
        
        # Add domain identifier to data for audit purposes (not exposed to client)
        df['_domain'] = self.domain
        df['_client_name'] = self.client_name
        
        return df
    
    def get_domain_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o domínio atual.
        
        Returns:
            Dicionário com informações do domínio
        """
        return {
            'domain': self.domain,
            'client_name': self.client_name,
            'sheet_id': self.sheet_id,
            'cache_timeout': self.domain_config.cache_timeout,
            'theme': self.domain_config.theme.to_dict(),
            'enabled': self.domain_config.enabled
        }
    
    def validate_data_isolation(self, df: pd.DataFrame) -> bool:
        """
        Valida que os dados pertencem apenas ao domínio atual.
        Verifica se não há vazamento de dados entre domínios.
        
        Args:
            df: DataFrame para validar
            
        Returns:
            True se os dados estão isolados corretamente
        """
        # Check if domain identifier is present and correct
        if '_domain' in df.columns:
            unique_domains = df['_domain'].unique()
            if len(unique_domains) == 1 and unique_domains[0] == self.domain:
                self.logger.debug(f"Data isolation validated for domain {self.domain}")
                return True
            else:
                self.logger.error(f"Data isolation violation detected for domain {self.domain}: found domains {unique_domains}")
                return False
        
        # If no domain identifier, assume data is isolated (for backward compatibility)
        self.logger.warning(f"No domain identifier found in data for domain {self.domain}")
        return True
    
    def invalidate_cache(self, operation: Optional[str] = None) -> bool:
        """
        Invalidate cache entries for this domain.
        
        Args:
            operation: Specific operation to invalidate, or None to invalidate all
            
        Returns:
            True if cache was invalidated successfully
        """
        if not self.cache_manager:
            self.logger.warning(f"No cache manager available for domain {self.domain}")
            return False
        
        try:
            if operation:
                # Invalidate specific operation
                cache_key = self.get_cache_key(operation)
                deleted = self.cache_manager.delete(self.domain, cache_key)
                if deleted:
                    self.logger.info(f"Invalidated cache for domain {self.domain}, operation: {operation}")
                else:
                    self.logger.debug(f"No cache entry found for domain {self.domain}, operation: {operation}")
                return deleted
            else:
                # Invalidate all cache for this domain
                cleared_count = self.cache_manager.clear_domain_cache(self.domain)
                self.logger.info(f"Cleared {cleared_count} cache entries for domain {self.domain}")
                return cleared_count > 0
        except Exception as e:
            self.logger.error(f"Failed to invalidate cache for domain {self.domain}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for this domain.
        
        Returns:
            Dictionary containing cache statistics
        """
        if not self.cache_manager:
            return {
                'cache_enabled': False,
                'message': 'Cache manager not available'
            }
        
        try:
            stats = self.cache_manager.get_cache_stats(self.domain)
            stats['cache_enabled'] = True
            stats['cache_timeout'] = self.domain_config.cache_timeout
            return stats
        except Exception as e:
            self.logger.error(f"Failed to get cache stats for domain {self.domain}: {e}")
            return {
                'cache_enabled': False,
                'error': str(e)
            }


def create_analyzer_for_domain(domain_config: DomainConfig, cache_manager: Optional[DomainCacheManager] = None) -> MultiDomainDataAnalyzer:
    """
    Factory function to create a MultiDomainDataAnalyzer for a specific domain.
    
    Args:
        domain_config: Configuration for the domain
        cache_manager: Optional cache manager for caching support
        
    Returns:
        Configured MultiDomainDataAnalyzer instance
    """
    return MultiDomainDataAnalyzer(domain_config, cache_manager)