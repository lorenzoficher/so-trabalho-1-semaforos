---
id: ISSUE-008
titulo: Escrever o relatório final com os números da bateria oficial
labels: [documentacao]
status: Concluída
task: T8
---

## Contexto

PRD, CA5. Entregável final pedido no enunciado: descrição da aplicação,
teste implementado, execução do experimento.

## Descrição

Escrever `docs/relatorio.md`, cobrindo:

- descrição do problema e por que ele exige semáforos (não só um lock);
- descrição dos três modos de sincronização;
- descrição dos testes (unitários e bateria);
- tabela com os números reais da ISSUE-007;
- conclusão sobre exclusão mútua, com base nos números, e não em suposição.

## Critérios de aceite

- [ ] Nenhum número no relatório é estimado, todos vêm de
  `results/battery_results.csv`.
- [ ] O relatório reproduz, em texto, a conclusão que os critérios de
  aceite do PRD (CA1 a CA3) pedem para provar.

## Dependências

ISSUE-007.
