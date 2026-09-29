---
id: glossario
pares:
  - de: "machine learning"
    para: "aprendizado de máquina"
  - de: "data governance"
    para: "governança de dados"
  - de: "data science"
    para: "ciência de dados"
---

# Glossário de terminologia (PT-BR)

Pares termo→termo preferido aplicados **deterministicamente** às saídas em
PT-BR após a geração (D-12/D-13). O payload é o frontmatter YAML acima; este
corpo é documentação para humanos.

## Como usar

- **Edite este arquivo e a próxima execução o vê** — a leitura é fresca a cada
  execução (sem cache). Cada par `{de, para}` é substituído mecanicamente no
  texto gerado, preservando a forma do termo encontrado (minúsculas,
  Capitalizada, ALL-CAPS), e toda substituição entra no relatório de QA
  (`qa.glossario`) com o número de ocorrências — nada é reescrito em silêncio.
- **Escolha os pares com conservadorismo**: liste apenas termos com
  equivalente PT-BR consolidado e estável (ex.: machine learning →
  aprendizado de máquina). O par é aplicado palavra por palavra, sem contexto
  — se a substituição pudesse mudar o sentido, não liste.
- **Termos técnicos consolidados SEM bom equivalente NÃO devem ser listados
  aqui** (ex.: Kubernetes, Python, backend): o QA de English bleed sinaliza
  termos em inglês como *aviso* não-bloqueante — nunca reescreve. A decisão
  de manter o termo em inglês é sua, avaliada antes de copiar.
