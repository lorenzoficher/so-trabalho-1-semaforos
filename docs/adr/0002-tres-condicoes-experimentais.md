# ADR 0002, Três condições experimentais, não duas

## Contexto

O objetivo mínimo do trabalho é comparar "sem semáforo" contra "com
semáforo". Isso poderia ser feito com só duas condições: `none` (nada) e
`full` (tudo). Mas com apenas essas duas, uma divergência de checksum no
modo `none` tem mais de uma causa possível ao mesmo tempo: pode ser porque
os índices de leitura e escrita entraram em corrida, ou pode ser porque
nada impedia os produtores de ultrapassar a capacidade do buffer e
atropelar itens ainda não consumidos, um problema de capacidade, não de
exclusão mútua.

## Decisão

Existe uma terceira condição, `counting`: os semáforos contadores `empty` e
`full` ficam ativos (a capacidade do buffer é respeitada, produtores esperam
por espaço, consumidores esperam por item), mas o semáforo binário `mutex`
não. A única coisa removida de `counting` para `full` é a exclusão mútua
sobre os índices.

Isso isola a variável: se `counting` também diverge tanto quanto `none`,
a causa da divergência é a exclusão mútua, não a capacidade, porque a
capacidade já estava garantida em `counting` e mesmo assim o resultado
diverge.

## Consequências

- O experimento tem três execuções por bateria em vez de duas, com o custo
  correspondente de tempo de execução da bateria completa.
- O relatório final precisa reportar e comparar as três condições, não só
  duas, para que a conclusão sobre exclusão mútua se sustente.
- A tabela de resultados (`docs/relatorio.md`) usa `counting` como a
  comparação principal contra `full`, e `none` como um caso extremo adicional
  (o pior cenário possível), não como a única evidência da causa.
