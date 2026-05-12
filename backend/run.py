"""
bibsimples Backend - Script de Execução Cross-Platform
===================================================

Este script inicia o servidor de desenvolvimento de forma
compatível com Windows, Linux e macOS.

Uso:
    python run.py
    python run.py --port 3000
    python run.py --host 0.0.0.0 --port 8080

Variáveis de ambiente:
    BIBSIMPLES_DEBUG - Se true, ativa reload automático
    BIBSIMPLES_PORT  - Porta do servidor (padrão: 8000)
    BIBSIMPLES_HOST  - Host do servidor (padrão: 127.0.0.1)
"""

import argparse
import os
import sys


def main():
    """Ponto de entrada principal."""
    
    # Argumentos de linha de comando
    parser = argparse.ArgumentParser(
        description="Inicia o servidor bibsimples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python run.py                    # Desenvolvimento (localhost:8000)
    python run.py --port 3000        # Porta customizada
    python run.py --host 0.0.0.0     # Acessível externamente
        """,
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("BIBSIMPLES_HOST", "127.0.0.1"),
        help="Host do servidor (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("BIBSIMPLES_PORT", "8000")),
        help="Porta do servidor (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.environ.get("BIBSIMPLES_DEBUG", "").lower() == "true",
        help="Ativar reload automático (default: BIBSIMPLES_DEBUG)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Número de workers (default: 1, não usar com --reload)",
    )
    
    args = parser.parse_args()
    
    # Importa uvicorn aqui para dar erro mais cedo se não estiver instalado
    try:
        import uvicorn
    except ImportError:
        print("Erro: uvicorn não está instalado.")
        print("Execute: pip install uvicorn[standard]")
        sys.exit(1)
    
    # Configuração do uvicorn
    config = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "log_level": "debug" if args.reload else "info",
    }
    
    # Workers só funciona sem reload
    if not args.reload and args.workers > 1:
        config["workers"] = args.workers
    
    # Banner
    print("=" * 60)
    print("bibsimples Backend")
    print("=" * 60)
    print(f"Host:   {args.host}")
    print(f"Port:   {args.port}")
    print(f"Reload: {args.reload}")
    print(f"URL:    http://{args.host}:{args.port}")
    print(f"Docs:   http://{args.host}:{args.port}/docs")
    print("=" * 60)
    print()
    
    # Inicia servidor
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
