---
id: ISSUE-003
titulo: Implementar CLI main.py com uma linha de resultado por execução
labels: [implementacao, cli]
status: Concluída
task: T3
---

## Contexto

`plan.md`, seção 5. É a forma de rodar uma única execução manualmente, para
inspeção e para uso no README.

## Descrição

Criar `src/main.py` com `argparse`: flag obrigatória `--mode`
(`none`/`counting`/`full`), flags opcionais `--producers`, `--consumers`,
`--items-per-producer`, `--buffer-size`, todas com o valor padrão fixo
definido em `spec.md` seção 4. Imprime uma linha de texto com todos os
campos de `ExperimentResult`.

## Critérios de aceite

- [ ] `python -m src.main --mode full` roda uma execução e imprime uma
  linha de resultado sem exigir nenhuma outra flag.
- [ ] Valores padrão de produtores/consumidores/itens/capacidade são os
  mesmos independentemente do `--mode` escolhido (RNF2 do PRD).

## Dependências

ISSUE-002.
