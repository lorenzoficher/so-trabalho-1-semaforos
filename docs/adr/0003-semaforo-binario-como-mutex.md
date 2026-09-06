# ADR 0003, Semáforo binário como mutex, em vez de `threading.Lock`

## Contexto

Python já tem `threading.Lock`, que resolveria a exclusão mútua do modo
`full` com a mesma eficácia prática de um semáforo binário. O enunciado,
porém, pede explicitamente o uso de semáforos, propostos por Dijkstra, e não
apenas "algum mecanismo de exclusão mútua".

## Decisão

O modo `full` usa um terceiro `threading.Semaphore(1)` (chamado `mutex`)
para a exclusão mútua, em vez de `threading.Lock()`. Isso deixa explícito,
lendo o código, que a mesma primitiva (semáforo) serve tanto para contar
recursos (`empty`/`full`, contagem inicial maior que 1) quanto para excluir
mutuamente (`mutex`, contagem inicial igual a 1), e que a diferença entre os
dois papéis está inteiramente no valor inicial e em como é usado, não na
primitiva em si.

## Consequências

- Do ponto de vista de comportamento, não muda nada: um `threading.Semaphore`
  inicializado com 1 se comporta como uma trava binária.
- Do ponto de vista didático, fica documentado no próprio código, sem
  precisar de comentário extra, que o trabalho usa semáforos para as duas
  finalidades pedidas no enunciado (P e V de Dijkstra), e não confunde
  semáforo contador com mutex, distinção que o enunciado e a spec
  (`docs/spec/spec.md`, seção 3) tratam como central.
