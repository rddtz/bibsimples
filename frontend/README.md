# bibsimples Frontend

Interface React para o bibsimples.

## Tecnologias

- **React 18** - UI Library
- **TypeScript** - Tipagem estática
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Query** - Data fetching/caching
- **React Router** - Navegação
- **Zustand** - State management

## Desenvolvimento

```bash
# Instalar dependências
npm install

# Servidor de desenvolvimento
npm run dev

# Build de produção
npm run build

# Preview do build
npm run preview
```

O servidor de desenvolvimento roda em `http://localhost:3000` e faz proxy das requisições `/api` para o backend em `http://127.0.0.1:8000`.

## Estrutura

```
src/
├── components/     # Componentes reutilizáveis
│   └── Layout.tsx  # Layout principal com sidebar
├── pages/          # Páginas/rotas
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── SearchPage.tsx
│   └── CatalogPage.tsx
├── services/       # Comunicação com API
│   └── api.ts
├── stores/         # Estado global (Zustand)
│   └── authStore.ts
├── hooks/          # Custom hooks
├── App.tsx         # Rotas
├── main.tsx        # Entry point
└── index.css       # Estilos globais + Tailwind
```

## Configuração

O frontend usa variáveis de ambiente via Vite:

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
```

> Em rede/local diferente, ajuste `VITE_API_PROXY_TARGET` para o host do backend bibsimples.

## Desenvolvimento Backend

Para desenvolver com o backend local:

1. Inicie o backend: `cd ../backend && python run.py`
2. Inicie o frontend: `npm run dev`
3. O Vite fará proxy das requisições automaticamente
