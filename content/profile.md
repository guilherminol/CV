---
example: true
name: "Ana Exemplo"
contact:
  email: "ana.exemplo@example.com"
  location: "São Paulo, SP"
summary:
  pt-BR: "Engenheira de IA sênior com foco em IA generativa, construindo produtos de ponta a ponta: backend, frontend e a infraestrutura que sustenta esses serviços."
  en: "Senior AI engineer focused on generative AI, building products end to end: backend, frontend, and the infrastructure that supports those services."
experiences:
  - company: "Exemplo IA"
    title:
      pt-BR: "Engenheira de IA Sênior"
      en: "Senior AI Engineer"
    location: "São Paulo, SP"
    start_date: "2022-03"
    end_date: null
    description:
      pt-BR: "Lidera a plataforma de IA generativa da empresa: pipelines de RAG, APIs de geração com streaming e as interfaces web que os times internos usam todos os dias; cuida também da infraestrutura que roda esses serviços."
      en: "Leads the company's generative-AI platform: RAG pipelines, streaming generation APIs, and the web interfaces internal teams use every day; also owns the infrastructure those services run on."
    impacts:
      - action:
          pt-BR: "Implementou um pipeline RAG com avaliação automática de qualidade de respostas"
          en: "Implemented a RAG pipeline with automated answer-quality evaluation"
        metric:
          pt-BR: "-40% no tempo de resposta e +25% de respostas aprovadas na avaliação"
          en: "-40% response time and +25% answers approved in evaluation"
        context:
          pt-BR: "Plataforma de atendimento interno usada por 200+ funcionários"
          en: "Internal support platform used by 200+ employees"
      - action:
          pt-BR: "Projetou a API de geração com streaming de tokens e medição de uso"
          en: "Designed the generation API with token streaming and usage metering"
        metric:
          pt-BR: "3 produtos internos passaram a reutilizar a mesma API"
          en: "3 internal products adopted the same API"
        context:
          pt-BR: "Contratos versionados e validação estrita das respostas do modelo"
          en: "Versioned contracts and strict validation of model responses"
      - action:
          pt-BR: "Conteinerizou e automatizou o deploy dos serviços de IA"
          en: "Containerized and automated deployment of the AI services"
        metric:
          pt-BR: "Deploy de 30 minutos para 5 minutos, com rollback em um comando"
          en: "Deploy went from 30 to 5 minutes, with one-command rollback"
        context:
          pt-BR: "Docker e CI com revisão automática de configuração"
          en: "Docker and CI with automated configuration review"
  - company: "Cloud Software Ltda."
    title:
      pt-BR: "Engenheira de Software Full-Stack"
      en: "Full-Stack Software Engineer"
    location: "São Paulo, SP"
    start_date: "2019-01"
    end_date: "2022-02"
    description:
      pt-BR: "Desenvolveu APIs e interfaces web para produtos B2B, do banco de dados ao deploy; estruturou a base de observabilidade do time."
      en: "Built APIs and web interfaces for B2B products, from database to deployment; established the team's observability baseline."
    impacts:
      - action:
          pt-BR: "Modularizou o monólito de faturamento em serviços com contratos claros"
          en: "Broke the billing monolith into services with clear contracts"
        metric:
          pt-BR: "Tempo médio de release caiu de 2 semanas para 2 dias"
          en: "Average release time dropped from 2 weeks to 2 days"
        context:
          pt-BR: "Migração feita sem interrupção do serviço"
          en: "Migration done with zero service interruption"
      - action:
          pt-BR: "Criou a biblioteca de componentes usada por todas as frentes web"
          en: "Created the component library used by every web team"
        metric:
          pt-BR: "-60% de código duplicado de interface"
          en: "-60% duplicated interface code"
        context:
          pt-BR: "React e TypeScript com testes de regressão visual"
          en: "React and TypeScript with visual regression tests"
      - action:
          pt-BR: "Implementou monitoramento e alertas para os serviços críticos"
          en: "Implemented monitoring and alerting for critical services"
        metric:
          pt-BR: "Tempo médio para detectar incidentes caiu de horas para minutos"
          en: "Mean time to detect incidents dropped from hours to minutes"
        context:
          pt-BR: "Dashboards e logs estruturados como padrão do time"
          en: "Dashboards and structured logs as a team standard"
  - company: "Tech Solutions ME"
    title:
      pt-BR: "Desenvolvedora de Software"
      en: "Software Developer"
    start_date: "2016-07"
    end_date: "2018-12"
    description:
      pt-BR: "Construiu aplicações web para clientes de varejo, cuidando do backend, do frontend e da integração com meios de pagamento."
      en: "Built web applications for retail clients, owning backend, frontend, and payment integrations."
    impacts:
      - action:
          pt-BR: "Integrou meios de pagamento com retry idempotente"
          en: "Integrated payment providers with idempotent retries"
        metric:
          pt-BR: "Falhas de cobrança dupla reduzidas a zero em 12 meses"
          en: "Double-charge failures reduced to zero in 12 months"
        context:
          pt-BR: "Integração com 2 provedores de pagamento"
          en: "Integration with 2 payment providers"
      - action:
          pt-BR: "Automatizou a suíte de testes de ponta a ponta da loja online"
          en: "Automated the end-to-end test suite of the online store"
        metric:
          pt-BR: "Cobertura de testes subiu de 12% para 70%"
          en: "Test coverage rose from 12% to 70%"
        context:
          pt-BR: "Pipeline de CI rodando a cada pull request"
          en: "CI pipeline running on every pull request"
education:
  - institution: "Universidade Exemplo"
    degree: "Bacharelado em Ciência da Computação"
    start_date: "2012-02"
    end_date: "2016-12"
skills:
  - category: "linguagens"
    items: ["Python", "TypeScript", "SQL"]
  - category: "frameworks"
    items: ["FastAPI", "React", "Pydantic", "Tailwind CSS"]
  - category: "ferramentas"
    items: ["Docker", "Git", "pytest", "Vite"]
  - category: "cloud"
    items: ["AWS", "Docker Compose", "GitHub Actions", "Nginx"]
certifications:
  - name: "AWS Certified Solutions Architect – Associate"
    issuer: "Amazon Web Services"
    year: "2023"
languages:
  - name: "Português"
    level: "nativo"
  - name: "Inglês"
    level: "avançado"
projects:
  - name: "Assistente de Documentos Internos"
    description:
      pt-BR: "Chat de IA generativa que responde perguntas sobre documentos internos com citação das fontes."
      en: "Generative-AI chat that answers questions over internal documents with cited sources."
    technologies: ["FastAPI", "pgvector", "React"]
    impacts:
      - action:
          pt-BR: "Reduziu o tempo de busca por informações internas"
          en: "Reduced the time spent searching internal information"
        metric:
          pt-BR: "~15h economizadas por semana no time"
          en: "~15h saved per week across the team"
        context:
          pt-BR: "Projeto interno usado por todos os times de produto"
          en: "Internal project used by every product team"
  - name: "Painel de Métricas de Serviços"
    description:
      pt-BR: "Painel web com métricas de saúde e custo dos serviços de IA em tempo quase real."
      en: "Web dashboard with near-real-time health and cost metrics for the AI services."
    technologies: ["React", "Vite", "FastAPI"]
    impacts: []
---

Perfil de exemplo do Career Tailor — substitua pelos seus dados reais (remova a marcação `example: true` quando fizer isso).
