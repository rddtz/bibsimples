# bibsimples

Interface simplificada para o Biblivre, focada nas operações do dia a dia da biblioteca escolar: catalogar livros, pesquisar o acervo e gerenciar exemplares.

---

## Requisitos

- Python 3.11+
- Node.js 18+
- Biblivre 5 rodando na mesma máquina (em `http://localhost:8080/Biblivre5`)

---

## Instalação (primeira vez)

### 0. Instalar Python e Node.js

Esses dois programas precisam ser instalados antes de qualquer coisa. Só precisa ser feito uma vez.

**Python:**

1. Acesse https://www.python.org/downloads/ e clique em **"Download Python 3.x.x"**
2. Execute o instalador
3. **IMPORTANTE:** na primeira tela, marque a caixa **"Add Python to PATH"** antes de clicar em Install
4. Clique em **"Install Now"** e aguarde

Para confirmar que funcionou, abra o Prompt de Comando (`Win + R` → digite `cmd` → Enter) e rode:
```
python --version
```
Deve aparecer algo como `Python 3.11.x`.

---

**Node.js:**

1. Acesse https://nodejs.org/ e clique no botão de download da versão **LTS**
2. Execute o instalador e clique em Next em todas as telas (as opções padrão estão corretas)
3. Aguarde a instalação terminar

Para confirmar, no Prompt de Comando:
```
node --version
```
Deve aparecer algo como `v20.x.x`.

> **Nota:** Após instalar Python ou Node.js, feche e abra novamente o Prompt de Comando para que eles sejam reconhecidos.

---

### 1. Baixar o código

**Opção A — via Git (recomendado para receber atualizações facilmente):**

1. Acesse https://git-scm.com/download/win e baixe o instalador
2. Execute e clique em Next em todas as telas (as opções padrão estão corretas)
3. Abra o Prompt de Comando e rode:

```
git clone https://github.com/seu-usuario/bibsimples.git
cd bibsimples
```

**Opção B — baixar o ZIP:**

1. Acesse a página do projeto no GitHub
2. Clique em **Code → Download ZIP**
3. Extraia o ZIP em uma pasta de sua escolha (ex: `C:\bibsimples`)
4. Abra o Prompt de Comando e navegue até a pasta:

```
cd C:\bibsimples
```

---

### 2. Configurar o backend

Entre na pasta `backend`:

```
cd backend
```

Crie o ambiente virtual e instale as dependências:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copie o arquivo de configuração:

```
copy .env.example .env
```

Abra o `.env` em qualquer editor de texto e ajuste:

```
# URL do Biblivre — deixe assim se ele roda na mesma máquina na porta padrão
BIBSIMPLES_BIBLIVRE_URL=http://localhost:8080/Biblivre5/

# Schema do Biblivre — deixe vazio para instalações padrão
BIBSIMPLES_BIBLIVRE_SCHEMA=
```

> Se o Biblivre usa uma porta diferente (ex: 80 ou 8180), ajuste apenas o número.

---

### 3. Compilar o frontend

Entre na pasta `frontend`:

```
cd ..\frontend
npm install
npm run build
```

Isso gera os arquivos do site dentro de `backend\static\`.  
**Só precisa ser feito uma vez** (ou quando atualizar o código).

---

### 4. Pronto

Volte para a raiz do projeto e dê duplo clique em **`iniciar.bat`**.

O sistema abre automaticamente no navegador em `http://localhost:8765`.

Para fechar, feche a janela de terminal que foi aberta.

---

## Uso no dia a dia

Basta dar duplo clique em **`iniciar.bat`**. O navegador abre sozinho.

---

## Personalizar as categorias CDD

O arquivo de categorias fica em:

```
frontend\src\data\cddPresets.csv
```

Abra em qualquer editor de texto (ex: Bloco de Notas). O formato é simples — uma categoria por linha:

```
codigo,Nome da categoria
869.0(81),Romance Brasileiro
981,História do Brasil
```

Linhas que começam com `#` são comentários e são ignoradas.

Após editar, recompile o frontend:

```
cd frontend
npm run build
```

---

## Atualizar o sistema

```
git pull
cd frontend
npm install
npm run build
cd ..\backend
venv\Scripts\activate
pip install -r requirements.txt
```

Depois use o `iniciar.bat` normalmente.

---

## Estrutura do projeto

```
bibsimples/
├── iniciar.bat          ← duplo clique para abrir o sistema
├── backend/
│   ├── .env             ← configurações (URL do Biblivre, etc.)
│   ├── app/             ← código do servidor
│   ├── static/          ← frontend compilado (gerado pelo npm run build)
│   └── venv/            ← ambiente Python (gerado na instalação)
└── frontend/
    ├── src/
    │   └── data/
    │       └── cddPresets.csv  ← lista de categorias CDD
    └── ...
```

---

## Solução de problemas

**O sistema não abre / página em branco**
- Verifique se o Biblivre está rodando: abra `http://localhost:8080/Biblivre5` no navegador
- Verifique se a URL no `.env` está correta

**"Python não encontrado"**
- Reinstale o Python marcando a opção **"Add Python to PATH"**

**"npm não encontrado"**
- Instale o Node.js em https://nodejs.org e abra um novo terminal

**Frontend não aparece (só a API responde em `/docs`)**
- O frontend não foi compilado. Entre em `frontend\` e rode `npm run build`
