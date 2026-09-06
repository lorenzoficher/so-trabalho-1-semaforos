---
id: ISSUE-001
titulo: Implementar BoundedBuffer e SyncMode com os três modos de sincronização
labels: [implementacao, core]
status: Concluída
task: T1
---

## Contexto

Base de todo o experimento (`spec.md`, seções 1 a 3; `plan.md`, seção 3).
Sem essa peça nenhuma outra issue pode começar.

## Descrição

Criar `src/buffer.py` com:

- `enum SyncMode`: `NONE`, `COUNTING`, `FULL`.
- `class BoundedBuffer`: recebe capacidade e modo no construtor, expõe
  `put(item)` e `get()`. Internamente mantém `_slots`, `_write_index`,
  `_read_index`, e cria `_empty`/`_full`/`_mutex` conforme o modo (`None`
  quando o modo não usa aquele semáforo).

## Critérios de aceite

- [ ] Nos três modos, a mesma assinatura `put`/`get` funciona sem lançar
  exceção quando o número de `put` e `get` respeita a capacidade e é feito
  em uma thread só.
- [ ] No modo `full`, `put` seguido de `get` (em uma thread só, dentro da
  capacidade) sempre devolve o valor inserido, na ordem de inserção.
- [ ] O código de `put`/`get` deixa explícito, com um comentário curto, qual
  linha é a seção crítica que o `mutex` protege (a leitura, cálculo e
  escrita do índice).
- [ ] Um `time.sleep(0)` (cede a GIL, não dorme de fato) entre a leitura e a
  gravação do índice torna a janela da corrida observável de forma
  confiável nos modos `NONE`/`COUNTING`, sem alterar o resultado do modo
  `FULL` (ver `docs/adr/0001-escolha-da-linguagem-python.md`).

## Dependências

Nenhuma.
