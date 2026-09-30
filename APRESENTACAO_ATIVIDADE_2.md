# Apresentação da Atividade 2

## Guia do Turista Inteligente

### Duração sugerida

- 4 minutos: demonstração do fluxo e dos seis testes
- 5 minutos: explicação técnica, cerca de 1 minuto e 40 segundos por pessoa
- 1 minuto: perguntas finais e encerramento

## Divisão entre os três integrantes

| Integrante | Parte principal | Arquivos para mostrar |
| --- | --- | --- |
| Pessoa 1 | Autenticação, APIs externas e geolocalização | `services.py`, `config.py` |
| Pessoa 2 | Clima, percurso, backend, sessões, persistência e resiliência | `app.py`, `services.py`, `static/data/viagens.json` |
| Pessoa 3 | Gemini, interface e demonstração | `planejamento.py`, `templates/index.html`, `static/js/app.js` |


## Explicação de cada integrante

O professor pediu domínio individual dos quatro eixos. Como somos três pessoas, a Pessoa 2 também explica o eixo de JSON e resiliência.

### Pessoa 1 — APIs REST, geocodificação e autenticação

> Eu fiquei responsável pela autenticação, pelo consumo das APIs e pela localização das cidades. No arquivo `services.py`, uso o `httpx.Client` para fazer as requisições e configurar timeouts. Isso evita que uma API lenta trave toda a aplicação.
>
> No login Google, o navegador envia o token para o backend. O sistema consulta o endpoint `tokeninfo`, verifica se o token é válido, confere o campo `aud` e compara esse valor com o `GOOGLE_CLIENT_ID`. Só depois disso o usuário é colocado na sessão Flask.
>
> Também sou responsável pelo geocoding. A aplicação consulta o Open-Meteo com filtro para o Brasil, obtém latitude, longitude e o estado real no campo `admin1`. Isso permite corrigir uma UF digitada incorretamente. Por exemplo, se eu informar Teresina com a UF RJ, o sistema reconhece que a cidade pertence ao Piauí e apresenta Teresina - PI.
>
> Se a cidade não existir ou não corresponder à UF informada, a aplicação interrompe a criação e mostra uma mensagem de erro. Na demonstração, vou entrar como visitante, testar Teresina com RJ e mostrar essa correção.

### Pessoa 2 — Telemetria, backend, sessões, JSON e resiliência

> Eu fiquei responsável pelo backend e pela persistência dos dados. A rota `POST /viagens/criar` recebe o formulário, chama os serviços, monta o roteiro e redireciona para a página inicial usando Post/Redirect/Get. Isso evita que atualizar a página envie o mesmo formulário novamente.
>
> Também explico as sessões do Flask. No modo visitante, a aplicação cria uma sessão temporária e guarda os roteiros em memória. Quando o visitante sai, essa sessão e seus dados temporários são removidos.
>
> Na parte de telemetria, o Open-Meteo fornece temperatura, umidade e vento. O OSRM calcula distância e duração do percurso. Se o clima falhar, aparecem valores `N/D`; se não houver rota rodoviária, aparece uma mensagem de contingência.
>
> O arquivo `static/data/viagens.json` tem usuários, roteiros, localização, telemetria e status dos serviços. O `threading.Lock` protege a leitura e a escrita para evitar corrupção em acessos simultâneos. Também explico a sanitização, o bloqueio de requisições duplicadas e os handlers de erro 404 e 405.

### Pessoa 3 — Gemini, interface e demonstração

> Eu fiquei responsável pelo guia turístico gerado pela IA e pela interface. O prompt recebe a cidade e a UF depois que elas são validadas. Ele pede atrações, atividades e gastronomia específicas do destino, evitando frases genéricas ou recomendações de outra cidade.
>
> A aplicação tenta modelos Gemini Flash alternativos quando um deles está indisponível. Se a chave for inválida, ocorrer erro, cota, demora excessiva ou resposta vazia, o sistema usa um fallback estruturado e não apresenta erro 500. O diagnóstico fica registrado no JSON.
>
> Depois que o guia é gerado, ele é salvo em `dicas_destino` e aparece no accordion do cartão de viagem. Na interface, também mostro clima, percurso e status dos serviços. O JavaScript desabilita o botão durante o envio para evitar cliques duplicados.

### Transição

> Primeiro eu mostro como a identidade e a localização são validadas. Depois, a Pessoa 2 explica como o backend reúne os dados e salva o roteiro. Por fim, a Pessoa 3 mostra como a IA transforma o destino em um guia turístico e como esse resultado aparece na tela.

## Demonstração dos seis testes

Faça a demonstração com uma viagem válida já preparada e deixe uma segunda aba aberta para `/viagens/json`.

| Ordem | Integrante | Procedimento | Explicação | Resultado esperado |
| --- | --- | --- | --- | --- |
| 1. Autenticação | Pessoa 1 | Abrir `/auth/demo`, criar uma sessão visitante e depois mostrar o botão de saída. | Sessão isolada para testes locais e remoção dos dados temporários no logout. | Usuário `Viajante Convidado`; logout remove a sessão e os dados temporários. |
| 2. Fallback da IA | Pessoa 3 | Explicar que uma chave inválida ou API indisponível aciona o fallback; não expor chave real na tela. | Continuidade da aplicação, guia estruturado e diagnóstico registrado. | Sem erro 500; `fallback_utilizado: true` no JSON. |
| 3. 404 e 405 | Pessoa 2 | Abrir `/rota-inexistente` e depois `/viagens/criar` com GET. | Handlers globais interceptam rotas inexistentes e métodos incorretos. | Redirecionamento para `/`. |
| 4. Cliques duplicados | Pessoa 3 | Preencher o formulário e clicar rapidamente mais de uma vez em **Gerar Guia**. | Botão desabilitado no frontend e lock com janela de requisições recentes no backend. | Um único roteiro criado. |
| 5. UF e destino sem rota | Pessoa 1 e Pessoa 2 | Informar `Teresina / RJ` como origem e `Fernando de Noronha / PE` como destino. | Geocoding corrige a UF pelo `admin1`; OSRM informa quando não existe estrada direta. | Teresina identificada como PI; percurso real ou fallback descritivo, conforme resposta do OSRM. |
| 6. JSON e integridade | Pessoa 2 | Clicar em **Ver JSON (API)** e abrir `/viagens/json`. | Endpoint expõe provedores, metadados, telemetria e status de cada serviço. | `200`, `application/json`, schema hierárquico e roteiro registrado. |

### Divisão do tempo da demonstração

1. **0:00–0:30 — Pessoa 1:** apresenta o problema e entra como visitante.
2. **0:30–1:30 — Pessoa 1:** executa login, geocoding e UF divergente.
3. **1:30–2:30 — Pessoa 2:** mostra clima, percurso, 404/405 e JSON.
4. **2:30–3:30 — Pessoa 3:** mostra geração do guia, fallback da IA e bloqueio de cliques.
5. **3:30–4:00 — Todos:** retomam o fluxo e respondem perguntas rápidas.

### Pontos técnicos para perguntas

- **Resiliência da IA:** chamada isolada, limite de tempo, modelos alternativos e fallback estruturado.
- **Validação de cidade:** Open-Meteo precisa localizar o nome informado e a UF; sem correspondência, a criação é interrompida.
- **Divisão entre três pessoas:** Pessoa 2 acumula backend/sessões e JSON/resiliência por serem partes do mesmo fluxo de orquestração e persistência.
- **Concorrência:** locks protegem a escrita do JSON e a criação contra ações simultâneas.
---

### 1 — Nome e proposta

#### Conteúdo

**Guia do Turista Inteligente**

Uma aplicação web que reúne localização, clima, percurso e inteligência artificial para ajudar no planejamento de viagens pelo Brasil.

### Explicação

> Nosso projeto é um planejador de viagens. O usuário informa uma cidade de origem e uma cidade de destino. A aplicação consulta APIs reais para descobrir a localização, o clima e o percurso, e usa o Gemini para gerar um guia turístico com atrações, culinária e uma dica de ouro.

**Responsável:** Pessoa 1.

---

### 2 — Problema resolvido

#### Conteúdo

O usuário normalmente precisa pesquisar em vários lugares:

- onde fica o destino;
- como estará o clima;
- qual é a distância;
- o que visitar e comer.

### Explicação

> A proposta foi concentrar essas informações em uma única tela. O sistema também apresenta os dados de forma organizada e mantém uma lista dos roteiros criados pelo usuário.

**Responsável:** Pessoa 1.

---

### 3 — Arquitetura do sistema

#### Conteúdo

```text
Usuário
   |
   v
Interface HTML + JavaScript
   |
   v
Flask: rotas, sessão e orquestração
   |
   +--> Google OAuth
   +--> Open-Meteo Geocoding
   +--> Open-Meteo Forecast
   +--> OSRM
   +--> Google Gemini
   |
   v
JSON de viagens + resposta renderizada
```

### Explicação

> O Flask funciona como o núcleo da aplicação. Ele recebe a solicitação do formulário, chama os serviços externos, monta um roteiro completo, salva os dados e devolve a página renderizada com Jinja2.

**Responsável:** Pessoa 2.

---

### 4 — Login, sessão e acesso à aplicação

#### Conteúdo

- Google Identity Services no navegador.
- `POST /auth/google/callback` no Flask.
- `verificar_token_google()` em `services.py`.
- Validação no endpoint `https://oauth2.googleapis.com/tokeninfo`.
- Comparação do campo `aud` com `GOOGLE_CLIENT_ID`.
- Sessão Flask em `session["usuario"]`.
- Modo visitante em `/auth/demo`.
- Endereço de demonstração: `http://localhost:8001`.
- O modo visitante permite testar a aplicação sem depender do Google OAuth.
- Para login Google, a origem `http://localhost:8001` precisa estar autorizada no Google Cloud.

### Explicação

> O frontend recebe a credencial do Google e envia o token para o backend. A validação acontece no Python, e não apenas no navegador. O sistema verifica se o token é válido, se possui usuário e se foi emitido para o Client ID correto. Para testes, existe também o modo visitante.

**Responsável:** Pessoa 1.

---

### 5 — Geolocalização

#### Conteúdo

Função: `buscar_coordenadas()`

- API: Open-Meteo Geocoding.
- Endpoint: `/v1/search`.
- Parâmetros: cidade, idioma, `count` e `country_codes=BR`.
- Resultado: latitude, longitude e `admin1`.
- Conversão de `admin1` para a UF oficial.
- A cidade precisa corresponder ao resultado encontrado.
- Cidade inexistente ou UF incompatível gera erro e não cria roteiro.
- Coordenadas `(0.0, 0.0)` são tratadas como falha.

### Demonstração conceitual

```text
Entrada: Teresina / RJ
Resultado real: Teresina / PI
```

### Explicação

> O estado informado pelo usuário não é aceito cegamente. A aplicação consulta a localização real e interpreta o estado retornado pela API. Por isso, mesmo com RJ informado no formulário, Teresina é reconhecida como pertencente ao Piauí.

**Responsável:** Pessoa 1.

---

### 6 — Clima e percurso

#### Conteúdo

**Clima**

- Open-Meteo Forecast.
- Temperatura, umidade e vento.
- Timeout defensivo de 4 segundos.
- Fallback com `N/D`.

**Percurso**

- OSRM Routing Engine.
- Coordenadas no formato longitude/latitude.
- Distância convertida de metros para quilômetros.
- Duração convertida para horas e minutos.
- Fallback: `Sem rota direta` e `Considere voos ou barcos`.

### Explicação

> Clima e percurso são serviços independentes. Se um deles falhar, o roteiro ainda pode ser criado com a informação de contingência. No caso de Fernando de Noronha, o comportamento observado do OSRM deve ser apresentado como resposta real da API, sem uma regra artificial criada especificamente para esse destino.

**Responsável:** Pessoa 2.

---

### 7 — Persistência e schema JSON

#### Conteúdo

O arquivo `static/data/viagens.json` possui:

- `versao_schema`;
- `atualizado_em`;
- `total_usuarios`;
- `total_roteiros`;
- `provedores`;
- `usuarios`.

Cada usuário possui:

- `perfil`;
- `metadados`;
- `roteiros`.

Cada roteiro possui:

- origem e destino;
- `geolocalizacao`;
- `telemetria.clima`;
- `telemetria.percurso`;
- `dicas_destino`;
- `metadados.status_requisicao`;
- `metadados.status_servicos`.

### Explicação

> A persistência é feita em JSON para manter uma estrutura simples e visível. A leitura usa `json.load`, a escrita usa `json.dump` com indentação de dois espaços e o acesso ao arquivo é protegido por `lock_arquivo_json`.

**Responsável:** Pessoa 2.

---

### 8 — Gemini e fallback

#### Conteúdo

Função: `obter_guia_destino_com_diagnostico()`

- SDK: `google-genai`.
- Chave: `GEMINI_API_KEY`.
- Modelos Flash com fallback de disponibilidade: `gemini-2.5-flash`, `gemini-3.5-flash` e `gemini-3.6-flash`.
- Prompt usa cidade e UF validadas e solicita atividades específicas, atrações e culinária.
- O prompt proíbe respostas genéricas e troca do destino.
- Resposta em texto puro com emojis.
- Limpeza de Markdown residual em `limpar_formato_texto()`.
- `ThreadPoolExecutor` com timeout operacional de 30 segundos.
- Fallback estruturado para chave inválida, cota, indisponibilidade, timeout ou erro.

### Explicação

> O Gemini melhora a parte turística do roteiro, mas não é um ponto único de falha. Se a chave estiver inválida, um modelo estiver indisponível ou a API não responder, o sistema tenta outro modelo Flash e, se necessário, entrega um guia alternativo estruturado, evitando um erro HTTP 500.

**Responsável:** Pessoa 3.

---

### 9 — Caminho do guia até a tela

#### Conteúdo

```text
Gemini
  -> planejamento.py
  -> app.py
  -> dicas_destino
  -> roteiro JSON
  -> Jinja2
  -> index.html
  -> usuário
```

### Explicação

> Não basta gerar o texto no backend. O guia precisa atravessar todas as camadas e aparecer visualmente. No nosso fluxo, o texto é salvo em `dicas_destino`, chega ao template Jinja2 e aparece no accordion do roteiro.

**Responsável:** Pessoa 3.

---

### 10 — Interface e experiência do usuário

#### Conteúdo

O cartão de viagem mostra:

- localização, cidade, UF e coordenadas;
- temperatura, umidade e vento;
- distância e duração;
- status dos serviços;
- guia turístico, atrações, culinária e dica de ouro.

O JavaScript também:

- abre e fecha o accordion;
- desabilita o botão durante o processamento;
- mostra um spinner textual;
- bloqueia cliques duplicados;
- recupera o botão após a navegação.

### Explicação

> A interface foi feita para apresentar o resultado por níveis. O resumo mostra clima e percurso; ao abrir o cartão, o usuário vê localização, status e o conteúdo completo do guia.

**Responsável:** Pessoa 3.

---

### 11 — Rotas principais

| Método | Rota | Função |
| --- | --- | --- |
| GET | `/` | Página principal |
| POST | `/auth/google/callback` | Valida login Google |
| GET | `/auth/demo` | Cria sessão visitante |
| GET/POST | `/auth/logout` | Encerra sessão |
| POST | `/viagens/criar` | Cria um roteiro |
| POST | `/viagens/deletar/<id>` | Exclui um roteiro |
| GET | `/viagens/json` | Retorna o JSON da aplicação |

### Explicação

> A criação utiliza POST e depois redireciona para a página inicial. Isso segue o padrão Post/Redirect/Get e evita que a atualização da página repita o envio do formulário.

**Responsável:** Pessoa 2.

---

### 12 — Segurança, falhas e concorrência

#### Conteúdo

- Sanitização contra HTML e caracteres de controle.
- Limite de tamanho para entradas.
- Timeouts em chamadas externas.
- Tratamento de falhas HTTP e respostas inválidas.
- `lock_arquivo_json` para leitura e escrita.
- `lock_requisicoes` para evitar chamadas simultâneas.
- Proteção contra requisições recentes duplicadas.
- Handlers para 404 e 405.

### Explicação

> O projeto considera que APIs externas podem falhar e que o usuário pode clicar mais de uma vez. Por isso, existem fallbacks, locks, timeouts e handlers de erro. A aplicação continua apresentando uma resposta controlada em vez de quebrar com erro 500.

**Responsável:** Pessoa 2.

---

### 13 — Demonstração ao vivo

### Ordem recomendada

1. Abrir `http://localhost:8001`.
2. Entrar como visitante.
3. Informar origem e destino.
4. Clicar em **Gerar Guia com APIs & IA**.
5. Abrir o cartão criado.
6. Mostrar localização, coordenadas, clima e percurso.
7. Mostrar o guia turístico gerado ou o fallback.
8. Abrir **Ver JSON (API)**.

### Testes rápidos

| Teste | Resultado esperado |
| --- | --- |
| Teresina / RJ | Localização reconhecida como PI |
| Chave Gemini inválida ou API indisponível | Fallback sem HTTP 500 |
| `GET /viagens/criar` | 405 tratado e redirecionamento |
| URL inexistente | 404 tratado e redirecionamento |
| Clique duplo | Um único roteiro criado |
| Fernando de Noronha / PE | Mostrar `Sem rota direta` quando o OSRM não encontrar estrada |

### Cuidados durante a demonstração

- Não exibir a chave `GEMINI_API_KEY`.
- Preferir **Entrar como Visitante** para a demonstração, evitando bloqueios de origem do Google.
- Se usar login Google, abrir exatamente `http://localhost:8001`.
- Deixar as APIs carregarem antes de clicar novamente.
- Se o Gemini estiver indisponível, explicar o fallback em vez de interromper a apresentação.
- Mostrar o JSON apenas depois de criar um roteiro.

**Responsável:** Pessoa 3 coordena; cada integrante explica sua própria parte.

---

### 14 — Testes e validação

### Validações realizadas

```bash
.venv/bin/python -m compileall app.py services.py planejamento.py config.py
```

### Resultado

> A compilação e a renderização Flask passaram. Também foram validados os métodos HTTP, o endpoint JSON, o fluxo de visitante, o fallback do Gemini, a correção de Teresina para PI e a presença dos dados na interface.

> A integração com APIs externas depende de conexão, credenciais e disponibilidade dos provedores no momento da demonstração.

---

### 15 — Conclusão

#### Conteúdo

- Integração de APIs reais.
- Autenticação e sessões.
- Persistência estruturada em JSON.
- IA generativa com fallback.
- Interface server-side com JavaScript.
- Tratamento de erros e concorrência.

### Explicação

> O resultado é uma aplicação completa, não apenas uma coleção de funções. O usuário entra, cria um roteiro, recebe dados reais de localização, clima e percurso, consulta um guia turístico e consegue visualizar e gerenciar seus roteiros.

### Encerramento

> Obrigado. Podemos mostrar o código de qualquer uma das integrações ou executar novamente a demonstração.

---

## Perguntas prováveis do professor

### Por que validar o Google no backend?

Porque o frontend pode ser manipulado. A validação no Python confirma o token diretamente no serviço oficial e compara o `aud` com o Client ID esperado.

### O que acontece se uma API externa cair?

Cada serviço possui timeout e tratamento de falha. O clima usa `N/D`, o percurso usa uma mensagem de contingência e o Gemini usa um guia fallback.

### Por que usar `POST` para criar?

Porque a criação altera dados. O fluxo usa POST/Redirect/GET, evitando que a atualização da página repita o envio do formulário.

### Como o sistema evita duplo clique?

O JavaScript desabilita o botão após o primeiro envio e o backend mantém locks e uma janela de requisições recentes por usuário.

### Onde o guia gerado aparece?

O texto sai de `planejamento.py`, é recebido em `app.py`, salvo em `dicas_destino` e renderizado por Jinja2 no accordion de `templates/index.html`.

### O sistema depende apenas do Gemini?

Não. O Gemini é responsável pelo texto turístico. Localização, clima e percurso continuam sendo obtidos por APIs específicas e independentes.

## Checklist antes da apresentação

- [ ] Ativar o ambiente virtual.
- [ ] Conferir `GEMINI_API_KEY` sem mostrar a chave para a sala.
- [ ] Instalar dependências com `.venv/bin/python -m pip install -r requirements.txt`.
- [ ] Iniciar `.venv/bin/python app.py`.
- [ ] Confirmar `http://localhost:8001`.
- [ ] Usar **Entrar como Visitante** para iniciar a demonstração.
- [ ] Se usar Google, cadastrar `http://localhost:8001` nas origens autorizadas.
- [ ] Cada integrante saber explicar seus arquivos.
- [ ] Criar um roteiro antes da apresentação.
- [ ] Deixar o navegador e o terminal prontos.
- [ ] Ter o fallback preparado caso alguma API externa falhe.
