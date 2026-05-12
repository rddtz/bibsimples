# bibsimples

Interface moderna para o sistema Biblivre.

## 🎯 Sobre

bibsimples é uma aplicação que funciona como intermediária entre o usuário e o Biblivre, oferecendo:

- **Interface moderna** - UI limpa e responsiva com React + TailwindCSS
- **Estabilidade** - Usa a API JSON interna do Biblivre (não web scraping)
- **Código Cutter local** - Geração sem dependência de sites externos
- **Consistência** - Dados sempre sincronizados com o Biblivre

## 📁 Estrutura

```
bibsimples/
├── backend/          # API FastAPI (Python)
│   ├── app/          # Código principal
│   │   ├── biblivre/ # Cliente para Biblivre
│   │   ├── api/      # Endpoints REST
│   │   └── utils/    # Utilitários (Cutter, etc.)
│   └── tests/        # Testes
├── frontend/         # UI React (TypeScript)
│   ├── src/          # Código fonte
│   └── dist/         # Build de produção
└── docs/             # Documentação
```

## 🚀 Início Rápido

### Requisitos

- Python 3.11+
- Node.js 18+ (para desenvolvimento frontend)
- Servidor Biblivre 5.x rodando

### Backend

```bash
cd backend

# Crie ambiente virtual
python3 -m venv venv

# Ative o ambiente (Windows)
venv\Scripts\activate

# Ative o ambiente (Linux/Mac)
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt

# Copie e configure o .env
cp .env.example .env
# Edite .env com suas configurações
# Exemplo para Biblivre em outro computador:
# BIBSIMPLES_BIBLIVRE_URL=http://172.16.3.208:8080/Biblivre5

# Execute
python run.py
```

Acesse: http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Instale dependências
npm install

# Servidor de desenvolvimento
npm run dev

# Build de produção
npm run build
```

Acesse: http://localhost:3000

### Testes

```bash
cd backend

# Todos os testes
pytest

# Com cobertura
pytest --cov=app
```

## 📖 API

### Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | /api/v1/auth/login | Login no Biblivre |
| POST | /api/v1/auth/logout | Logout |
| POST | /api/v1/catalog/books | Catalogar livro + exemplares |
| GET | /api/v1/search | Pesquisar acervo |
| POST | /api/v1/utils/cutter | Gerar código Cutter |
| POST | /api/v1/utils/book-code | Gerar código do livro |

Veja documentação completa em `/docs` após iniciar o servidor.

## 🛠️ Tecnologias

### Backend
- **FastAPI** - Framework web assíncrono
- **httpx** - Cliente HTTP async
- **Pydantic** - Validação de dados
- **pytest** - Testes

### Frontend
- **React 18** - UI Library
- **TypeScript** - Tipagem estática
- **TailwindCSS** - Estilização
- **Vite** - Build tool
- **React Query** - Data fetching
- **Zustand** - Estado global

## 📝 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas!
