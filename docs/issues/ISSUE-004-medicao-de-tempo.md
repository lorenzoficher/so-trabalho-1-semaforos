---
id: ISSUE-004
titulo: Medir tempo de execução por condição
labels: [medicao]
status: Concluída
task: T4
---

## Contexto

O enunciado pede, quando possível, a medição do tempo de execução em cada
condição.

## Descrição

`run_experiment` (ISSUE-002) mede o tempo entre o início da criação das
threads e o `join` da última thread, com `time.perf_counter()` (relógio
monotônico de alta resolução, apropriado para medir duração, ao contrário
de `time.time()`), e devolve o valor em milissegundos como parte do
`ExperimentResult`.

## Critérios de aceite

- [ ] O tempo medido não inclui a montagem do `ExperimentConfig` nem a
  impressão do resultado, só a fase concorrente (criação das threads até o
  último `join`).
- [ ] O tempo aparece tanto na saída do `main.py` (uma execução) quanto na
  saída agregada de `battery.py` (média, mínimo, máximo por modo).

## Dependências

ISSUE-002.
