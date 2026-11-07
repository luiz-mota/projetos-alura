# Agents — MDBank (sistema multiagente)

Projeto do curso da Alura sobre agentes ([alura-cursos/curso-alura](https://github.com/alura-cursos/curso-alura), branch `feature/modulo1`).
Um banco fictício, o **MDBank**, atende clientes por chat. O atendimento é dividido entre agentes especialistas, que se comunicam por protocolos abertos:

| Protocolo | Para que serve aqui |
|---|---|
| **MCP** (Model Context Protocol) | Expõe *tools*, *resources* e *prompts* do "backend do banco" para os agentes |
| **A2A** (Agent2Agent) | Cada agente publica um **AgentCard** com as próprias *skills*, e o supervisor conversa com ele por esse protocolo |
| **AG-UI** (Agent–User Interaction) | Streaming de eventos (texto e estado) do supervisor para o frontend |

> Base de estudo. O objetivo é entender a arquitetura e depois reaproveitá-la em um projeto pessoal.

---

## Arquitetura

```
                ┌──────────────┐      ┌──────────────────┐
  usuário ───▶  │ frontend     │      │ frontend2 (React)│
                │ Streamlit    │      │ AG-UI events     │
                │ :9090        │      │ :3000            │
                └──────┬───────┘      └────────┬─────────┘
                POST /chat                POST / (SSE)
                       ▼                       ▼
                ┌─────────────────────────────────────┐
                │ supervisor  :8080                   │
                │  LLM roteador → LangGraph (Send)    │
                └──────┬───────────────────┬──────────┘
                    A2A│                   │A2A
                       ▼                   ▼
          ┌──────────────────┐   ┌──────────────────────┐
          │ abrir_conta :8081│   │ cartao_credito :8082 │
          │ LangChain agent  │   │ LangChain agent      │
          └────────┬─────────┘   └─────────┬────────────┘
                MCP│ (http /mcp_gateway)   │MCP
                   └──────────┬────────────┘
                              ▼
                ┌──────────────────────────────┐
                │ recursos :8084 (FastMCP)     │
                │ tools · resources · prompts  │
                │ persistência em db.json      │
                └──────────────────────────────┘

                ┌──────────────────────────────┐
                │ bfa :8083                    │  descobre agentes (AgentCards)
                │ registry + busca BM25        │  e tools (/tools do MCP) e
                └──────────────────────────────┘  resolve a melhor skill p/ query
```

O fluxo de uma mensagem é este:
1. O frontend envia o texto ao **supervisor**.
2. O supervisor pede a um LLM roteador (`gpt-4o`, temperatura 0) que devolva um JSON `{"agents": [...]}`.
3. Para cada agente escolhido, o LangGraph dispara um `Send` para o nó correspondente, e o nó chama o agente via **A2A**.
4. O agente (LangChain `create_agent`) usa as tools do servidor **MCP** `recursos` para consultar e criar contas e cartões.
5. As respostas são concatenadas e devolvidas ao usuário (ou transmitidas em streaming como eventos AG-UI).

---

## Componentes

### `recursos/` — servidor MCP (FastMCP)
- **Resources:** `conta://{cpf}` e `cartao://{cpf}` (leitura de dados).
- **Prompts:** `abrir_conta_prompt` e `solicitar_cartao_prompt` (templates de mensagens).
- **Tools:**

  | Tool | O que faz |
  |---|---|
  | `consultar_conta(cpf)` | `{existe: bool, conta?}` |
  | `consultar_cartao(cpf)` | `{existe: bool, cartao?}` |
  | `criar_ou_buscar_conta(nome, cpf)` | Cria a conta (número aleatório, saldo 0) ou retorna a existente |
  | `solicitar_cartao(cpf, tipo)` | Exige que a conta exista e emite o cartão (limite aleatório de 1000 a 5000) |
  | `gerar_prompt_abertura(nome, cpf)` | Renderiza o prompt MCP `abrir_conta_prompt` |

- As tools leem os dados pelos próprios resources (`ctx.read_resource`), e não direto do dicionário.
- A rota customizada `GET /tools` lista as tools com `tags` e `examples` nas *annotations*. O `bfa` usa essa lista.
- Os dados ficam em `/app/db.json`, que, por causa do volume, é `recursos/db.json` no host (ignorado pelo git).

### `agents/abrir_conta/` e `agents/cartao_credito/` — agentes A2A
Cada agente tem três camadas, e esse é o padrão para criar novos agentes:

| Arquivo | Papel |
|---|---|
| `agent/*.py` | Lógica do agente: `init_chat_model` + `MultiServerMCPClient` (tools do MCP) + `create_agent` com system prompt + `InMemorySaver` (memória por `thread_id`) |
| `executor.py` | `AgentExecutor` do A2A: recebe o input do usuário, chama `run_agent` e coloca a resposta na `EventQueue` |
| `server.py` | Define a `AgentSkill` (id, tags, exemplos) e o `AgentCard`, e sobe o app com `A2AStarletteApplication` |

O AgentCard fica em `http://<agente>:8000/.well-known/agent-card.json`. É ali que o supervisor e o bfa descobrem o agente.

### `supervisor/` — orquestrador
- `src/agents.py`: o roteador, um LLM sem tools com saída JSON validada por `JsonOutputParser` e um modelo Pydantic (`RouterOutput`).
- `src/services.py`:
  - `request_agent`: cliente A2A (`A2ACardResolver` → `ClientFactory`), com cache por URL.
  - Grafo LangGraph: `START → (roteamento condicional com Send) → cartao_credito | abrir_conta → END`. O estado `responses` usa o reducer `add`, que acumula as respostas dos agentes executados em paralelo.
  - `executar_supervisor_stream`: a versão para AG-UI, que emite `TEXT_MESSAGE_*` e eventos `STATE_UPDATE`.
- `app.py`: `POST /chat` (resposta JSON) e `POST /` (AG-UI via SSE).

### `bfa/` — registro e descoberta de capacidades
- Na inicialização, descobre os agentes (lendo os AgentCards) e as tools (pelo `/tools` do MCP) e monta um registro único.
- Indexa nome, descrição e tags com **BM25** e expõe `/resolve?query=...`, `/resolve/agents`, `/resolve/tools`, `/skills`.
- Serve como alternativa ao roteamento por LLM: escolhe o agente ou a tool por busca lexical, sem custo de LLM.

### `frontend/` (Streamlit) e `frontend2/` (React + AG-UI)
- `frontend`: um chat simples que chama `supervisor:8000/chat`.
- `frontend2`: consome `http://localhost:8080/` e mostra os eventos e o estado compartilhado (`StatusPanel`, `EventStream`).

---

## Como rodar

Pré-requisitos: Docker Desktop e uma chave da OpenAI.

```bash
# 1. criar o .env em cada serviço que usa LLM (veja .env.example)
cp .env.example agents/abrir_conta/.env
cp .env.example agents/cartao_credito/.env
cp .env.example supervisor/.env
# edite os três arquivos e coloque sua OPENAI_API_KEY

# 2. subir tudo
docker compose up --build
```

| URL | Serviço |
|---|---|
| http://localhost:9090 | Chat Streamlit |
| http://localhost:3000 | Chat React (AG-UI) |
| http://localhost:8080/docs | Supervisor (Swagger) |
| http://localhost:8081/.well-known/agent-card.json | AgentCard abrir_conta |
| http://localhost:8082/.well-known/agent-card.json | AgentCard cartao_credito |
| http://localhost:8083/skills | Registro do bfa |
| http://localhost:8084/tools | Tools do MCP |

### Roteiro de teste

```text
Quero abrir uma conta
Meu nome é Levina Passos
Meu CPF é 38888206850
Quero um cartão de crédito, meu CPF é 38888206850
meu cpf é 000.000.000-00 me de os detalhes do cartao
```

Testes do BFA (`http://localhost:8083/resolve?query=...`):
- Cartão: `quero um cartao`, `me mostra opcoes de cartao`, `quero saber sobre cartao platinum`
- Conta: `quero abrir uma conta`, `preciso criar uma conta bancaria`, `abrir conta no banco`

---

## Observações e limitações (pontos para o projeto pessoal)

- **Memória compartilhada entre usuários:** `thread_id` é fixo em `"1"` nos agentes e no roteador, e o `session_id` do `ChatRequest` não é repassado.
- **Roteador sem validação:** se o LLM devolver um nome de agente que não existe, o `Send` falha. Seria melhor validar contra a lista de nós.
- **Inconsistência:** `abrir_conta` recria o agente a cada chamada, enquanto `cartao_credito` guarda um cache global.
- **O BFA não está integrado:** o supervisor usa um dicionário `AGENTS` fixo no código em vez de consultar o bfa.
- **Persistência simples:** `db.json` sem lock nem validação de CPF.
- **Schemas fixos no código** no `/tools` do `recursos` (`schema_map`), em vez de derivá-los das assinaturas.

---

## Progresso no curso

- [x] Módulo 1: MCP + agentes A2A + supervisor LangGraph + AG-UI + BFA
- [ ] Próximos módulos (adicionar conforme o curso avançar)
