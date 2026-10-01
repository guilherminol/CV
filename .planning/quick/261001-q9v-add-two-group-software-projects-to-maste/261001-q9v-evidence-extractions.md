# Evidence — repo extractions pasted by user (2026-10-01)

Verbatim extraction results the user obtained by running the extraction prompt inside the two Group Software repos. Grounding source for every number in CONTEXT.md. The extraction prompt's golden rule was: repo-verifiable facts only, no invention, unknowns flagged.

---

## gia-iebt — extração de currículo

### 1. Proposta e status

Sistema centralizador de MCPs (Model Context Protocol): interpreta a demanda do usuário dentro de uma conversa e roteia dinamicamente para o fluxo ou agente de IA correto com base no estado da conversa, não em uma árvore fixa de intenções. Está em desenvolvimento ativo, com pipeline de entrega configurado para três ambientes AWS (dev, staging, produção) via ECS, infraestrutura provisionada por Terraform e deploy manual controlado. Não há evidência de volume real de tráfego em produção no repositório — isso precisaria ser confirmado com o responsável pelo projeto. O desenvolvimento começou em julho de 2026 e segue ativo até o início de outubro de 2026, somando 408 commits em cerca de três meses.

### 2. Uso real e métricas

- 408 commits em ~3 meses de desenvolvimento.
- 120 migrations de banco de dados aplicadas.
- 21 entidades/tabelas de domínio modeladas (conversas, usuários, tentativas e sessões de login, memória de longo prazo, servidores e vínculos MCP, uso e custo de LLM, interações, invocações de tools, prompts, score de confiança, vínculos de identidade entre contas, entre outras).
- 290 arquivos de teste, somando 2.870 casos de teste automatizados.
- Gate de cobertura mínima de 90% obrigatório no pipeline de CI — o build quebra se cair abaixo disso.
- 28 especificações de implementação formalmente documentadas e versionadas (bootstrap do sistema, autenticação, memória de longo prazo, identidade canônica entre contas, múltiplos provedores de mensageria, red team de segurança, entre outras).
- 6 canais de entrada de conversa implementados: WhatsApp (via integração própria), WhatsApp via uazapi, WhatsApp/SMS via Twilio, Telegram, API de chat interna, e um canal de transbordo para atendimento humano.

### 3. Stack completa por camada

- Linguagem: Python 3.13.
- Framework web: FastAPI, servido via Uvicorn.
- Orquestração de conversa: LangGraph e LangChain, isolados atrás de uma interface própria para que o motor de orquestração possa ser trocado sem afetar o núcleo do sistema.
- LLM: OpenRouter como gateway único para múltiplos provedores (OpenAI, Anthropic, Google, modelos abertos), com comparação sistemática de modelos (GPT-5-mini, GPT-4.1-mini, Claude 3 Haiku, Gemini, Gemma).
- Banco de dados: PostgreSQL, acesso assíncrono via SQLAlchemy, migrations gerenciadas por Alembic.
- Cache/estado: Redis.
- Autenticação: JWT emitido pelo próprio sistema; dados sensíveis em repouso criptografados com Fernet.
- Infraestrutura/Deploy: containers Docker multi-stage, AWS via Terraform (ECS em EC2 atrás de load balancer, RDS PostgreSQL, ElastiCache Redis, banco vetorial Qdrant self-hosted, VPN overlay para acesso seguro a serviços MCP externos, segredos via SSM Parameter Store).
- CI/CD: pipeline self-hosted com lint (ruff + mypy) → testes com cobertura mínima de 90% → análise estática (SonarQube) → build de imagem Docker para arquitetura ARM64/Graviton → deploy manual por ambiente.
- Observabilidade: instrumentação OpenTelemetry sempre ativa (exportação para Datadog em produção) e plataforma própria de observabilidade de LLM (Langfuse) self-hosted, com stack dedicada de banco relacional, banco analítico e armazenamento de objetos.
- Armazenamento de arquivos: MinIO (compatível com S3) para áudio bruto recebido por voz, com troca transparente para S3 real em produção.
- Testes: pytest com suporte assíncrono e medição de cobertura — 290 arquivos, 2.870 casos.
- Qualidade de código: lint e formatação automatizados, tipagem estática, análise de complexidade, SonarQube.
- Documentação: geração automática de documentação técnica e de API (Swagger/ReDoc).

### 4. Integrações externas

- OpenRouter, como gateway único para chat e transcrição de voz com múltiplos provedores de LLM.
- WhatsApp por três vias distintas (integração própria, uazapi e Twilio, esta última com verificação de assinatura da requisição).
- Telegram, via API oficial de bots.
- Protocolo MCP real (múltiplos transportes), com registro de servidores MCP e controle de quais tools cada agente pode acessar, persistido em banco.
- Integrações de condomínio e de pessoas tratadas como "MCP" por convenção interna, mas implementadas como adapters REST específicos, não como protocolo MCP real.
- Langfuse (observabilidade de LLM) e Datadog (monitoramento de aplicação, apenas em produção).
- promptfoo, para benchmark comparativo de prompts/modelos e para testes de red team adversarial de segurança (cobrindo as principais categorias de ataque a sistemas de LLM, incluindo testes customizados de isolamento entre clientes, bypass de autenticação e abuso de código de verificação).

### 5. Arquitetura e destaques de engenharia

- Arquitetura hexagonal aplicada com rigor: bibliotecas de terceiros usadas para orquestração de IA ficam confinadas à camada de infraestrutura, nunca vazando para as camadas de domínio e aplicação.
- Multi-tenancy tratado como requisito arquitetural de segurança, não apenas de dado: o identificador do cliente é sempre resolvido no servidor por uma fonte confiável, nunca aceito cru vindo do canal de entrada, cobrindo leitura, escrita, cache, filas, logs, memória de longo prazo e descoberta de tools disponíveis.
- Identidade canônica global entre diferentes contas/clientes: a mesma pessoa é reconhecida de forma unificada entre produtos distintos, com resolução de conflitos por prioridade e sem fusão automática de contas.
- Centralização e auditoria de custo de uso de LLM por conversa, cliente e modelo, incluindo detecção automática (não baseada em lista fixa) de uso de LLM embutido dentro de tools de terceiros chamadas pelo sistema.
- Memória de longo prazo entre conversas, inspirada em arquiteturas do tipo MemGPT, com escopo isolado por cliente e por usuário.
- Testes de segurança automatizados (red teaming) rodando contra o sistema real, cobrindo especificamente tentativas de quebra de isolamento entre clientes, bypass de autenticação, abuso de código de verificação e injeção de instruções maliciosas.
- O ponto técnico mais difícil resolvido neste repositório é o roteamento dinâmico de conversas baseado em estado (em vez de árvore fixa de intenções) atravessando múltiplos agentes e canais simultaneamente, mantendo de forma consistente o histórico de chamadas de ferramentas entre turnos de conversa mesmo quando esse histórico precisa ser podado por limite de contexto.

### 6. Features principais

1. Atendimento conversacional multicanal (três integrações de WhatsApp, Telegram, API interna e transbordo para atendimento humano).
2. Autenticação do usuário com código de verificação e sessão controlada por token.
3. Roteamento dinâmico de intenção baseado no estado da conversa.
4. Memória de longo prazo entre conversas.
5. Identidade unificada do usuário entre diferentes contas/produtos.
6. Centralização e auditoria de custo de uso de LLM.
7. Observabilidade de execução de IA e benchmark comparativo de modelos/prompts.
8. Testes automatizados de segurança (red teaming) contra ataques típicos de sistemas de LLM.
9. Cadastro administrável de servidores MCP com controle granular de quais tools cada agente pode usar.
10. Transcrição de áudio enviado por voz, com armazenamento auditável.

---

## mcp-com — extração de currículo

### 1. Proposta e status

Servidor MCP (Model Context Protocol) que expõe as APIs de autoatendimento do ecossistema de gestão condominial como ferramentas (tools) consumíveis por agentes de IA. Está ativo, com pipeline de entrega automatizado que constrói e publica a imagem Docker e realiza deploy remoto controlado em uma única instância de servidor enxuta (sem balanceador de carga nem auto-scaling). Não há evidência de volume real de tráfego no repositório — precisaria ser confirmado com o responsável. Desenvolvimento iniciado em julho de 2026, com último commit no fim de setembro de 2026, somando 73 commits em cerca de dois meses e meio.

### 2. Uso real e métricas

- 73 commits em ~2,5 meses de desenvolvimento.
- 27 arquivos de teste automatizado, somando 250 casos de teste.
- 19 ferramentas (tools) MCP expostas no conjunto de produção.
- Relatório de cobertura de testes presente no repositório, porém desatualizado em relação ao último commit (não reflete o estado mais recente do código).

### 3. Stack completa por camada

- Linguagem: TypeScript, rodando em Node.js 18+.
- Protocolo: SDK oficial do Model Context Protocol.
- Servidor HTTP: Fastify, instrumentado com rastreamento distribuído.
- Validação: Zod, com schemas estritos de entrada e saída de cada ferramenta.
- Transportes: dois modos simultâneos — stdio para uso local/desenvolvimento e HTTP remoto sem estado para produção.
- Autenticação: dividida em duas camadas — chave de API para autenticar o cliente MCP que fala com o servidor, e token JWT do usuário final repassado por chamada de ferramenta (nunca exposto como parâmetro aberto).
- Assinatura de requisição: assinatura criptográfica (RSA com SHA-256) aplicada às chamadas feitas a um sistema parceiro de IA, garantindo autenticidade e integridade da requisição — reimplementando em TypeScript um protocolo de assinatura originalmente escrito em Java, mantendo compatibilidade byte a byte com o sistema legado.
- Observabilidade: rastreamento distribuído via OpenTelemetry, com visualização local via Jaeger.
- Infraestrutura: containers Docker, infraestrutura provisionada como código (Terraform) em uma única instância de servidor na nuvem, com registro de imagens e segredos geridos via serviço de parâmetros seguro.
- CI/CD: pipeline self-hosted com lint, testes, análise estática de qualidade (SonarQube), build de imagem e deploy remoto via comando administrativo seguro (sem Kubernetes/orquestrador de containers).
- Testes: Vitest com medição de cobertura.

### 4. Integrações externas

- API de autoatendimento do backend principal do ecossistema de gestão condominial, para login, dados de unidades, boletos, certidões e balancete.
- Sistema de IA conversacional parceiro, que consome este servidor MCP como cliente, com verificação de autenticidade de requisição via assinatura criptográfica.
- Jaeger, para rastreamento distribuído em ambiente de desenvolvimento.

### 5. Arquitetura e destaques de engenharia

- Arquitetura em camadas seguindo Domain-Driven Design e Arquitetura Hexagonal de forma estrita, com separação clara entre regras de domínio, casos de uso de aplicação e adaptadores de infraestrutura.
- Padrão de registro composto (composite) para as ferramentas MCP, permitindo agregar múltiplos conjuntos de ferramentas de diferentes origens por trás de uma única interface, sem alterar o núcleo do servidor.
- Separação de responsabilidade entre autenticação de transporte (chave de API) e autorização de negócio (token do usuário final), nunca misturadas no mesmo mecanismo.
- Assinatura criptográfica de requisições de saída para um sistema parceiro, reimplementando com fidelidade byte a byte um protocolo de assinatura originalmente em outra linguagem — exigindo engenharia reversa cuidadosa de um protocolo sem especificação formal compartilhada.
- Dois transportes de protocolo (local e remoto) servidos pelo mesmo núcleo de domínio e aplicação, sem duplicar lógica de negócio.
- O ponto técnico mais difícil resolvido neste repositório é manter contratos de ferramenta consistentes (validação estrita de entrada/saída, truncamento de conteúdo grande, paginação) funcionando de forma idêntica nos dois transportes e em múltiplos registries de ferramentas agregados, preservando o isolamento arquitetural entre o protocolo MCP e as regras de acesso à API de negócio.

### 6. Features principais

1. Autenticação e renovação de sessão do usuário.
2. Consulta de dados do usuário e das unidades do condomínio.
3. Listagem e emissão de boletos em PDF, incluindo versão agregada para múltiplas unidades.
4. Emissão de certidão de "nada consta", individual e agregada.
5. Consulta de balancete financeiro do condomínio, individual e agregado.
6. Busca de conhecimento/informações sobre o condomínio.
7. Exposição das ferramentas por dois modos de transporte (local e remoto), cobrindo cenários de uso diferentes.
