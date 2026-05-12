"""
bibsimples Backend - Configurações
===============================

Este módulo centraliza todas as configurações da aplicação usando
Pydantic Settings. As configurações podem vir de:

1. Variáveis de ambiente
2. Arquivo .env
3. Valores padrão definidos aqui

Uso:
    from app.config import settings
    
    print(settings.biblivre_url)
    print(settings.debug)

Notas sobre Windows:
    - pathlib.Path é usado para caminhos (cross-platform)
    - Não há dependência de variáveis de ambiente Unix-only
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação bibsimples.
    
    Todas as configurações podem ser sobrescritas via variáveis de ambiente
    ou arquivo .env. O prefixo BIBSIMPLES_ é usado para evitar conflitos.
    
    Exemplos de variáveis de ambiente:
        BIBSIMPLES_DEBUG=true
        BIBSIMPLES_BIBLIVRE_URL=http://localhost:8080/Biblivre5
        BIBSIMPLES_SECRET_KEY=minha-chave-secreta
    """
    
    # ==========================================================================
    # Configurações Gerais
    # ==========================================================================
    
    # Título exibido na documentação da API
    app_title: str = Field(
        default="bibsimples API",
        description="Título da aplicação exibido na documentação"
    )
    
    # Versão da API
    app_version: str = Field(
        default="0.1.0",
        description="Versão atual da API"
    )
    
    # Modo debug (mais logs, reload automático)
    debug: bool = Field(
        default=False,
        description="Ativa modo debug com mais logs e reload automático"
    )
    
    # ==========================================================================
    # Configurações do Biblivre
    # ==========================================================================
    
    # URL base do servidor Biblivre
    # Exemplo: http://localhost:8080/Biblivre5
    biblivre_url: str = Field(
        default="http://localhost/Biblivre5",
        description="URL base do servidor Biblivre (sem barra final)"
    )
    
    # Schema do Biblivre (geralmente "default")
    # Bibliotecas multi-schema podem ter nomes diferentes
    biblivre_schema: str = Field(
        default="default",
        description="Schema/instância do Biblivre a ser usada"
    )
    
    # Timeout para requisições ao Biblivre (em segundos)
    biblivre_timeout: float = Field(
        default=30.0,
        description="Timeout em segundos para requisições ao Biblivre"
    )
    
    # ==========================================================================
    # Segurança
    # ==========================================================================
    
    # Chave secreta para assinatura de tokens (gere uma aleatória em produção!)
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-USE-STRONG-RANDOM-KEY",
        description="Chave secreta para assinatura de tokens JWT"
    )
    
    # ==========================================================================
    # CORS (Cross-Origin Resource Sharing)
    # ==========================================================================
    
    # Origens permitidas para CORS (separadas por vírgula)
    # Use "*" para permitir todas (apenas em desenvolvimento!)
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Origens permitidas para CORS, separadas por vírgula"
    )
    
    # ==========================================================================
    # Cache Local (SQLite)
    # ==========================================================================
    
    # Caminho do banco de dados SQLite para cache
    # Usa pathlib para ser cross-platform
    cache_db_path: Path = Field(
        default=Path("data/cache.db"),
        description="Caminho do arquivo SQLite para cache local"
    )
    
    # Habilitar cache local
    cache_enabled: bool = Field(
        default=True,
        description="Habilita cache local em SQLite"
    )
    
    # ==========================================================================
    # Validadores
    # ==========================================================================
    
    @field_validator("biblivre_url")
    @classmethod
    def remove_trailing_slash(cls, v: str) -> str:
        """Remove barra final da URL do Biblivre se existir."""
        return v.rstrip("/")
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Valida e normaliza as origens CORS."""
        # Mantém como string, será parseado quando necessário
        return v.strip()
    
    # ==========================================================================
    # Propriedades Computadas
    # ==========================================================================
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Retorna lista de origens CORS."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def biblivre_base_url(self) -> str:
        """URL completa para requisições ao Biblivre."""
        return f"{self.biblivre_url}/{self.biblivre_schema}"
    
    # ==========================================================================
    # Configuração do Pydantic
    # ==========================================================================
    
    model_config = SettingsConfigDict(
        # Prefixo para variáveis de ambiente
        env_prefix="BIBSIMPLES_",
        
        # Arquivo .env para carregar configurações
        env_file=".env",
        
        # Encoding do arquivo .env
        env_file_encoding="utf-8",
        
        # Ignora campos extras em variáveis de ambiente
        extra="ignore",
        
        # Case insensitive para variáveis de ambiente
        case_sensitive=False,
    )


# Instância global de configurações
# Carrega automaticamente de variáveis de ambiente e .env
settings = Settings()
