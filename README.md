# Trabalho 1, Threads + Semáforos

Produtor-consumidor com buffer circular limitado, em Python
(`threading.Thread` e `threading.Semaphore`), implementado como um
experimento controlado: o programa prova, numericamente, que sem exclusão
mútua o buffer compartilhado se corrompe, e que com um semáforo binário ele
passa a ser sempre correto.

**Autor:** Lorenzo Ficher, disciplina de Sistemas Operacionais.

## Resultado em uma tabela

Bateria oficial, 30 execuções por modo, Windows 11 / Python 3.14.3:

| Modo | Semáforos ativos | Execuções | Divergentes | Tempo médio |
|:--|:--|--:|--:|--:|
| `full` | `empty`, `full`, `mutex` | 30 | **0** | 619,2 ms |
| `counting` | `empty`, `full` | 30 | **30** | 289,1 ms |
| `none` | nenhum | 30 | **30** | 107,2 ms |

Relatório completo, com a explicação de cada modo e a análise dos números:
[`docs/relatorio.md`](docs/relatorio.md). Enunciado original:
[`docs/Enunciado.md`](docs/Enunciado.md).

## Requisitos

- Python 3.10 ou mais recente.
- `pytest` (`pip install -r requirements.txt`), só para os testes.
- Nenhuma outra dependência, nenhum compilador, nenhum WSL. Roda direto no
  Windows, no diretório deste projeto.

## Como executar

```powershell
# suite completa de testes deterministicos (14 testes)
python -m pytest tests/ -v

# so os testes da API do buffer (10 testes)
python -m pytest tests/test_buffer.py -v

# uma execucao isolada, por modo
python -m src.main --mode full
python -m src.main --mode counting
python -m src.main --mode none

# bateria oficial (30 execucoes por modo, grava results/battery_results.csv)
python tests/battery.py
```

Cada execução isolada imprime uma linha assim:

```text
modo=full produzido=50005000 consumido=50005000 diferenca=0 duplicados=0 nao_escritos=0 tempo_ms=612.632
```

## Os três modos de sincronização

Único parâmetro que muda entre execuções comparáveis. Número de produtores,
consumidores, itens e capacidade do buffer ficam fixos por padrão
(configuráveis via flags, ver `python -m src.main --help`).

| `--mode` | Capacidade garantida | Exclusão mútua | O que falta |
|:--|:--:|:--:|:--|
| `full` | sim | sim | nada, é a referência |
| `counting` | sim | **não** | só o semáforo binário `mutex` |
| `none` | não | não | tudo |

A razão de existirem três condições, e não só duas, está em
`docs/adr/0002-tres-condicoes-experimentais.md`: `counting` isola a exclusão
mútua como a variável responsável pela corrupção, separado do problema de
capacidade do buffer.

## Estrutura

```
.
├── PRD.md                    # requisitos e criterios de aceitacao
├── docs/
│   ├── Enunciado.md          # enunciado original, nao editar
│   ├── relatorio.md          # entregavel, descricao + testes + resultados
│   ├── spec/                 # spec, plan e tasks (padrao SDD)
│   ├── issues/                # uma issue por tarefa, rastreavel ate o PRD
│   └── adr/                  # decisoes de arquitetura e seus porques
├── src/
│   ├── buffer.py              # BoundedBuffer, SyncMode, os tres semaforos
│   ├── experiment.py          # produtores, consumidores, checksum, tempo
│   └── main.py                 # CLI, uma execucao por chamada
├── tests/
│   ├── test_buffer.py          # testes deterministicos da API (10)
│   ├── test_experiment.py      # validacao de entrada de run_experiment (4)
│   └── battery.py              # bateria oficial, 30 execucoes por modo
└── results/
    └── battery_results.csv     # gerado por tests/battery.py
```

Toda a decisão sobre exclusão mútua está em `src/buffer.py`, nas chamadas de
`acquire`/`release` sobre `_mutex`, dentro de `BoundedBuffer.put` e
`BoundedBuffer.get`.

## Metodologia (padrão SDD)

Este trabalho segue um fluxo de desenvolvimento guiado por especificação:
`PRD.md` define o problema, `docs/spec/spec.md` detalha o comportamento
esperado, `docs/spec/plan.md` detalha a arquitetura, `docs/spec/tasks.md`
quebra o plano em tarefas, e cada tarefa tem uma issue correspondente em
`docs/issues/`, rastreável de volta até o PRD. Decisões de projeto com
alternativas descartadas estão em `docs/adr/`.
