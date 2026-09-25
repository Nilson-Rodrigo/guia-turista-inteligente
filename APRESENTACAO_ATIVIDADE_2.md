# Apresentação: Guia do Turista Inteligente

## Organização da equipe

### Pessoa 1: APIs, autenticação e geolocalização

Explique que o Flask recebe o token do Google em `POST /auth/google/callback` e que `verificar_token_google()` valida o token no endpoint oficial `https://oauth2.googleapis.com/tokeninfo`. A função compara o campo `aud` com `GOOGLE_CLIENT_ID`, trata falhas sem gerar erro 500 e cria a sessão do usuário.

Mostre também `buscar_coordenadas()`, que consulta a API de Geocoding do Open-Meteo usando cidade, UF e `country_codes=BR`. O resultado fornece latitude, longitude e `admin1`; a UF é normalizada. O caso Teresina/RJ deve ser apresentado como evidência de correção para Teresina/PI.

### Pessoa 2: Clima, percurso e persistência

Apresente `obter_clima()`, que usa o Open-Meteo Forecast para temperatura, umidade e vento, com timeout e fallback `N/D`. Depois mostre `obter_percurso()`, que usa o OSRM, calcula distância em quilômetros e duração em horas/minutos. Quando a API não fornece rota, o sistema informa `Sem rota direta` e `Considere voos ou barcos`.

Explique a persistência em `app.py`: `sanitizar_entrada()`, `lock_arquivo_json`, `json.load`, `json.dump` com `indent=2`, além do schema com usuários, roteiros, geolocalização, telemetria e metadados. Destaque que o endpoint `GET /viagens/json` disponibiliza a estrutura em JSON.

### Pessoa 3: Gemini, Flask e interface

Explique que `obter_guia_destino_com_diagnostico()` usa o SDK `google-genai`, a variável `GEMINI_API_KEY`, o modelo `gemini-3.6-flash`, `ThreadPoolExecutor` e timeout de 6 segundos. O prompt pede atrações, culinária e dica de ouro em texto puro com emojis. Chave inválida, cota, erro ou timeout acionam o fallback estruturado.

Mostre o caminho completo: Gemini -> `planejamento.py` -> `app.py` -> `dicas_destino` -> `viagens.json` -> Jinja2 -> `templates/index.html`. Na tela, o accordion apresenta guia, localização, coordenadas, clima, percurso e status dos serviços. O JavaScript impede o duplo clique, desabilita o botão e exibe o processamento.

## Demonstração prática

1. Entrar como visitante em `/auth/demo`.
2. Criar um roteiro com origem e destino válidos.
3. Abrir o cartão salvo e mostrar localização, clima, percurso e guia.
4. Testar `Teresina / RJ` e mostrar a correção para `PI`.
5. Testar uma chave Gemini inválida e mostrar o fallback sem HTTP 500.
6. Acessar `/viagens/json` e mostrar schema, metadados e status dos serviços.
7. Tentar `GET /viagens/criar`: a rota deve responder com 405 tratado e redirecionar para `/`.
8. Abrir uma URL inexistente: o handler 404 redireciona para a página inicial.
9. Testar Fernando de Noronha/PE e relatar o comportamento real retornado pelo OSRM, sem criar regra artificial para o destino.

## Fechamento

O projeto integra autenticação, APIs REST, persistência JSON, IA generativa, tratamento de falhas e interface web. Cada integrante deve explicar sua função, mostrar a evidência no código e executar pelo menos um teste relacionado à sua parte.