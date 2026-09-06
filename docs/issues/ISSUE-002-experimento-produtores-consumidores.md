---
id: ISSUE-002
titulo: Implementar ExperimentConfig, ExperimentResult e run_experiment
labels: [implementacao, core]
status: Concluída
task: T2
---

## Contexto

`plan.md`, seção 4. Orquestra as threads produtoras e consumidoras em torno
do `BoundedBuffer` da ISSUE-001, e calcula a evidência de corrupção
(checksums, duplicados, leituras de slot vazio).

## Descrição

Criar `src/experiment.py` com:

- `ExperimentConfig` (dataclass): `mode`, `buffer_size`, `n_producers`,
  `n_consumers`, `items_per_producer`.
- `ExperimentResult` (dataclass): `mode`, `produced_checksum`,
  `consumed_checksum`, `duplicated_reads`, `unwritten_reads`, `elapsed_ms`.
- `run_experiment(config) -> ExperimentResult`: cria o buffer, dispara as
  threads produtoras (cada uma com uma faixa disjunta de inteiros) e as
  threads consumidoras (cada uma soma em um acumulador protegido por um
  `threading.Lock` próprio, independente do modo testado), mede o tempo com
  `time.perf_counter()`, e retorna o resultado.
- A janela de corrida é tornada observável em `BoundedBuffer` (ISSUE-001),
  não aqui: `run_experiment` só orquestra threads e mede tempo, sem tocar
  em detalhes de agendamento do interpretador.

## Critérios de aceite

- [ ] `produced_checksum` é calculado por fórmula fechada a partir da faixa
  de cada produtor, sem depender de acumulação concorrente.
- [ ] A soma de `consumed_checksum` usa um lock próprio, não um dos
  semáforos do buffer.
- [ ] Rodar com `mode=FULL` várias vezes seguidas sempre resulta em
  `produced_checksum == consumed_checksum`, `duplicated_reads == 0` e
  `unwritten_reads == 0`.
- [ ] Rodar com `mode=NONE` ou `mode=COUNTING` resulta em divergência na
  grande maioria das execuções (evidência estatística, não uma garantia
  determinística, isso é esperado e está documentado em `spec.md`).
- [ ] `n_producers < 1` ou `n_consumers < 1` levanta `ValueError` antes de
  criar qualquer thread, em vez de um `ZeroDivisionError` (achado da revisão
  de código, corrigido nesta entrega).

## Dependências

ISSUE-001.
