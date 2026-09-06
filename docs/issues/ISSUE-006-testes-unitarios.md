---
id: ISSUE-006
titulo: Implementar testes determinísticos da API do buffer
labels: [teste]
status: Concluída
task: T6
---

## Contexto

`spec.md`, seção 6. Separa defeito de estrutura de dados de defeito de
concorrência: se estes testes falharem, a causa não é sincronização entre
threads, porque eles rodam em uma thread só.

## Descrição

Criar `tests/test_buffer.py` com `pytest`, cobrindo, para os três modos:

- inserir um item e retirá-lo devolve o mesmo valor;
- a ordem de retirada é a ordem de inserção, com mais de um item;
- o buffer reaproveita corretamente os slots ao encher e esvaziar mais de
  uma vez (índice módulo capacidade);
- nenhuma exceção é lançada ao usar `put`/`get` dentro da capacidade, nos
  três modos.

## Critérios de aceite

- [ ] `python -m pytest tests/test_buffer.py` passa de forma determinística,
  em qualquer execução, sem depender de tempo ou agendamento.
- [ ] Os testes não criam threads (usam o buffer em uma thread só).

## Dependências

ISSUE-001.
