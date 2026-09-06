---
id: ISSUE-005
titulo: Implementar bateria de execuções e agregação em CSV
labels: [implementacao, medicao]
status: Concluída
task: T5
---

## Contexto

`spec.md`, seção 5. Uma execução isolada não prova nada sobre exclusão
mútua, é uma questão de frequência: a prova precisa de várias repetições por
modo.

## Descrição

Criar `tests/battery.py`: importa `run_experiment` diretamente (sem
subprocessos), roda `--repeticoes` vezes (padrão 30) para cada um dos três
modos, grava cada execução individual em `results/battery_results.csv`
(colunas: modo, repetição, checksum produzido, checksum consumido,
diferença, duplicados, não escritos, tempo em ms) e imprime, ao final, um
resumo por modo: quantas execuções tiveram diferença zero, quantas
divergiram, tempo médio, mínimo e máximo.

## Critérios de aceite

- [ ] `python tests/battery.py` roda sem argumentos, usando os padrões.
- [ ] O CSV gerado tem uma linha por execução individual (90 linhas para 30
  repetições em 3 modos).
- [ ] O resumo impresso no terminal é suficiente, sozinho, para preencher a
  tabela de resultados do relatório.
- [ ] `--repeticoes 0` (ou negativo) encerra com uma mensagem clara, em vez
  de um `IndexError` ao gravar o CSV (achado da revisão de código, corrigido
  nesta entrega).

## Dependências

ISSUE-002.
