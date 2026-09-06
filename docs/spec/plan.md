# Plano técnico, Produtor-Consumidor com Semáforos

Deriva de `spec.md`. Decisões de arquitetura relevantes viraram ADR em
`docs/adr/`.

## 1. Linguagem e primitivas

Python 3.10+, biblioteca padrão apenas para o código de produção
(`threading.Thread`, `threading.Semaphore`), `pytest` para os testes. Ver
`docs/adr/0001-escolha-da-linguagem-python.md` para a justificativa e para
como o experimento contorna o GIL.

`threading.Semaphore` do Python é a mesma primitiva de Dijkstra: `acquire()`
é P, `release()` é V, com contagem interna e fila de espera geridas pelo
interpretador (na CPython, apoiadas em uma condition variable de SO).

## 2. Estrutura de módulos

```
src/
  buffer.py       # BoundedBuffer e SyncMode
  experiment.py   # ExperimentConfig, ExperimentResult, run_experiment
  main.py         # CLI: uma execução, imprime uma linha de resultado
tests/
  test_buffer.py  # testes determinísticos da API do buffer
  battery.py      # roda o experimento N vezes por modo, agrega e salva CSV
```

## 3. `BoundedBuffer`

Estado: lista de tamanho fixo (`_slots`), `_write_index`, `_read_index`
(inteiros simples, não atômicos, de propósito), e até três semáforos
conforme o modo (`_empty`, `_full`, `_mutex`, `None` quando o modo não usa).

Pseudocódigo de `put(item)`:

```
se _empty existe: _empty.acquire()
se _mutex existe: _mutex.acquire()

indice = _write_index % capacidade
_slots[indice] = item
_write_index += 1

se _mutex existe: _mutex.release()
se _full existe: _full.release()
```

Pseudocódigo de `get()`:

```
se _full existe: _full.acquire()
se _mutex existe: _mutex.acquire()

indice = _read_index % capacidade
item = _slots[indice]
_read_index += 1

se _mutex existe: _mutex.release()
se _empty existe: _empty.release()

retorna item
```

No modo `none`, nenhum dos três `if` é executado: acesso direto, sem espera
e sem exclusão. No modo `counting`, `_empty`/`_full` existem mas `_mutex` é
`None`. No modo `full`, os três existem.

A linha `_write_index += 1` (e a equivalente de leitura) é o ponto exato da
corrida: em CPython ela se traduz em carregar o valor atual, somar 1 e
gravar de volta, três passos que podem ser interrompidos entre si. É essa
linha, e não o array em si, que o modo `full` protege com `_mutex`. Esse
ponto é documentado no código com um comentário curto, porque não é óbvio
para quem lê só a assinatura do método.

Entre a leitura do índice e a gravação no slot, há um `time.sleep(0)` (cede
a GIL, não dorme de fato). Sem ele, a janela da corrida existe mas é curta
demais para se manifestar de forma confiável em toda execução, como mostrou
um teste inicial com `sys.setswitchinterval()` reduzido (documentado em
`docs/adr/0001-escolha-da-linguagem-python.md`); com ele, o modo `counting`
diverge de forma consistente. O `sleep(0)` está no mesmo caminho de código
para os três modos, então é um custo constante presente em todas as
condições por igual, e não compromete a comparação de tempo entre elas.

## 4. `experiment.py`

`ExperimentConfig`: `mode`, `buffer_size`, `n_producers`, `n_consumers`,
`items_per_producer`.

Cada produtor `i` gera os inteiros de `i * items_per_producer + 1` até
`(i + 1) * items_per_producer`, uma faixa própria e disjunta. Isso permite
calcular o checksum produzido total por fórmula fechada, sem precisar
acumular nada durante a execução (o próprio cálculo do checksum produzido
não deve ser uma fonte de corrida).

Cada consumidor tenta `get()` um número fixo de vezes (total de itens
dividido pelo número de consumidores), e acumula o valor lido em um checksum
consumido compartilhado. Essa soma final usa um `threading.Lock` próprio,
independente do modo testado. Justificativa: o alvo do experimento é a
estrutura compartilhada do buffer (índices e slots), não a soma de
conferência; se a soma também corresse sem proteção, uma divergência
observada poderia vir da soma ou do buffer, e o experimento deixaria de
isolar uma única causa. Além do checksum, o consumidor também conta:

- leituras de slot com valor `None` (posição nunca escrita ainda, só
  possível no modo `none`);
- leituras duplicadas (mesmo valor lido mais de uma vez), detectadas ao
  final comparando a lista de valores lidos contra o conjunto de valores
  produzidos.

`run_experiment(config)` cria o buffer, inicia todas as threads produtoras
e consumidoras, aguarda todas terminarem (`join`), mede o tempo decorrido
com `time.perf_counter()`, e retorna um `ExperimentResult`.

## 5. `main.py`

CLI (`argparse`) que roda uma execução e imprime uma linha de resultado.
Parâmetros com valor padrão fixo (buffer 10, 4 produtores, 4 consumidores,
2500 itens por produtor, 10000 itens no total), sobrescrevíveis via flags,
conforme RNF2.

## 6. `tests/battery.py`

Roda `run_experiment` diretamente (em processo, sem subprocessos, mais
rápido) `--repeticoes` vezes (padrão 30) para cada um dos três modos, grava
cada execução em `results/battery_results.csv` e imprime um resumo por modo
(quantas divergiram, tempo médio/mínimo/máximo).

## 7. `tests/test_buffer.py`

Testes com `pytest`, todos em uma thread só, chamando `put`/`get`
diretamente dentro da capacidade do buffer (nunca bloqueiam), para os três
modos, conforme a seção 6 de `spec.md`.

## 8. Relação com as issues

Cada seção deste plano vira uma ou mais linhas de `tasks.md`, e cada linha
de `tasks.md` vira uma issue em `docs/issues/`.
