# 🇧🇷 Guia do Turista Inteligente (Flask + HTTPX + Google Auth + Gemini AI)

Aplicação web desenvolvida com o microframework **Flask** e Python moderno para orquestração de APIs externas com autenticação via **Google Identity Services (OAuth JWT)**, gerando roteiros de viagem com dados meteorológicos, cálculo de percurso rodoviário e guia turístico & culinário com inteligência artificial.

---

## 🚀 Como Executar o Projeto Localmente

### 1. Clonar o Repositório e Acessar a Pasta

```bash
git clone https://github.com/maykolsampaio/guia-turista-inteligente.git
cd guia-turista-inteligente
```

---

## 2. Criar o Ambiente Virtual (`.venv`)

Linux / macOS:

```bash
python3 -m venv .venv
```

Opcionalmente, ative o ambiente para usar `python` e `pip` diretamente:

```bash
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Execute cada comando separadamente. Não escreva `bash` antes de `python3`.

---

### 3. Instalar as Dependências

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

---

### 4. Configurar as Chaves e Variáveis de Ambiente

Configure as variáveis no seu terminal:

Linux / macOS:

```bash
export GEMINI_API_KEY="SUA_CHAVE_GEMINI_AQUI"
export GOOGLE_CLIENT_ID="418686361464-m2hip9tp1v15sr3lj14iip3q956c756g.apps.googleusercontent.com"
export PORT="8001"
```

No Google Cloud Console, em **APIs e serviços &gt; Credenciais &gt; ID do cliente OAuth 2.0**, adicione estas origens JavaScript autorizadas:

```text
http://localhost:8001
http://127.0.0.1:8001
```

Abra o sistema por `http://127.0.0.1:8001`. Como `localhost` e `127.0.0.1` são origens diferentes, use sempre o mesmo endereço que está cadastrado no Google Cloud. A origem precisa coincidir exatamente, incluindo protocolo, host e porta.

#### Diagnóstico do login Google

Foi identificado o erro `Erro 400: origin_mismatch` ao abrir o app por `http://localhost:8001`, enquanto o login funcionou por `http://127.0.0.1:8001`. O Google considera esses endereços origens distintas. Cadastre ambos no mesmo cliente OAuth do tipo **Aplicativo da Web** e abra o app usando exatamente uma das origens autorizadas. Para este projeto, o endereço confirmado é `http://127.0.0.1:8001`.

O fluxo do projeto usa o callback JavaScript do Google Identity Services: o navegador recebe a credencial e a envia ao Flask em `POST /auth/google/callback`. Portanto, a URI `/auth/callback` não corresponde a uma rota do app e não é usada por esse fluxo. Cadastre as origens JavaScript autorizadas; não é necessário cadastrar uma URI de redirecionamento para esse callback JavaScript.

Se o Google continuar exibindo `origin_mismatch`, confira se a origem foi salva no mesmo cliente cujo ID está sendo usado pelo app e se o endereço na barra do navegador, incluindo protocolo, host e porta, é idêntico ao cadastrado. O backend também compara o campo `aud` do token com `GOOGLE_CLIENT_ID`. Quando essa variável de ambiente está definida, ela substitui o valor padrão de `config.py`; configure-a com o ID do mesmo cliente OAuth exibido na página de login.

Windows (PowerShell):

```powershell
$env:GEMINI_API_KEY="SUA_CHAVE_GEMINI_AQUI"
$env:GOOGLE_CLIENT_ID="418686361464-m2hip9tp1v15sr3lj14iip3q956c756g.apps.googleusercontent.com"
$env:PORT="8001"
```

Para conferir se as variáveis foram carregadas no Linux/macOS:

```bash
.venv/bin/python -c 'import os; print("GEMINI_API_KEY:", "OK" if os.getenv("GEMINI_API_KEY") else "AUSENTE"); print("PORT:", os.getenv("PORT", "8001"))'
```

> **Obtenção da Chave Gemini:** Acesse o [Google AI Studio](https://aistudio.google.com/), crie sua chave e defina na variável `GEMINI_API_KEY`.

---

### 5. Iniciar o Servidor Flask

```bash
.venv/bin/python app.py
```

Acesse a aplicação no navegador em:  
👉 **`http://127.0.0.1:8001`**

---

## 📂 Estrutura do Projeto

```text
├── app.py                 # [A IMPLEMENTAR] Aplicação Flask (Autenticação Google no Python com Sessão, SSR e Rotas)
├── config.py              # Constantes, UFs do Brasil, Client ID do Google e variáveis de ambiente
├── services.py            # [A IMPLEMENTAR] Integrações com APIs externas via HTTPX (Open-Meteo, OSRM e validação de token Google OAuth)
├── planejamento.py        # [A IMPLEMENTAR] Módulo de IA Gemini para geração de guia turístico e gastronomia
├── templates/
│   └── index.html         # Frontend Server-Side Rendering (Jinja2, Google Login URI, Cards e Accordion)
├── static/
│   ├── css/style.css      # Estilização responsiva em CSS
│   ├── js/app.js          # Comportamento de interface (Accordion e bloqueio de cliques)
│   └── data/
│       ├── estados_brasil.json # Mapeamento oficial das 27 UFs do Brasil
│       └── viagens.json        # Persistência em JSON dos roteiros dos usuários logados
├── requirements.txt       # Lista de dependências Python
└── README.md              # Documentação e instruções de execução
```

---

## 🧪 Qualidade de Código e Linter

Para validar o código com as ferramentas da disciplina:

```bash
# Formatação e checagem de boas práticas (PEP 8)
ruff check . --fix

# Checagem estática de tipos (Type Hints)
mypy app.py services.py planejamento.py config.py
```
