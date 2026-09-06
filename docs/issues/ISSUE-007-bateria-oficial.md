---
id: ISSUE-007
titulo: Rodar a bateria oficial e coletar os números reais do experimento
labels: [medicao, experimento]
status: Concluída
task: T7
---

## Contexto

Nenhum número deste trabalho pode ser estimado ou inventado. O PRD (CA5)
exige números observados de fato.

## Descrição

Rodar `python tests/battery.py` nesta máquina (Windows, sem WSL, Python
3.14), com os parâmetros padrão, e guardar a saída (resumo por modo e
`results/battery_results.csv`) para uso em `docs/relatorio.md`.

## Critérios de aceite

- [ ] `results/battery_results.csv` existe e tem uma linha por execução
  individual.
- [ ] Os números citados em `docs/relatorio.md` batem exatamente com os do
  CSV gerado nesta execução.

## Dependências

ISSUE-005, ISSUE-006 (os testes precisam passar antes de a bateria ser
considerada válida).
