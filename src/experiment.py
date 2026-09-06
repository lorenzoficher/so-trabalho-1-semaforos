"""Orquestra produtores e consumidores em torno de um BoundedBuffer.

Mede a corrupcao do buffer compartilhado (checksum, duplicados, leituras de
slot vazio) e o tempo de execucao. Implementa ISSUE-002 e ISSUE-004.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from src.buffer import BoundedBuffer, SyncMode


@dataclass
class ExperimentConfig:
    mode: SyncMode
    buffer_size: int = 10
    n_producers: int = 4
    n_consumers: int = 4
    items_per_producer: int = 2500

    @property
    def total_items(self) -> int:
        return self.n_producers * self.items_per_producer


@dataclass
class ExperimentResult:
    mode: SyncMode
    produced_checksum: int
    consumed_checksum: int
    duplicated_reads: int
    unwritten_reads: int
    elapsed_ms: float

    @property
    def difference(self) -> int:
        return self.consumed_checksum - self.produced_checksum

    @property
    def is_correct(self) -> bool:
        return (
            self.difference == 0
            and self.duplicated_reads == 0
            and self.unwritten_reads == 0
        )


def _producer(buffer: BoundedBuffer, start: int, count: int) -> None:
    for value in range(start, start + count):
        buffer.put(value)


def _consumer(
    buffer: BoundedBuffer,
    count: int,
    collected: list,
    collected_lock: threading.Lock,
) -> None:
    local_values = [buffer.get() for _ in range(count)]
    # Lock proprio da instrumentacao, independente do modo testado
    # (docs/spec/plan.md, secao 4): nao faz parte do fenomeno sob teste.
    with collected_lock:
        collected.extend(local_values)


def run_experiment(config: ExperimentConfig) -> ExperimentResult:
    if config.n_producers < 1 or config.n_consumers < 1:
        raise ValueError("n_producers e n_consumers precisam ser >= 1")
    if config.total_items % config.n_consumers != 0:
        raise ValueError("total_items (producers * items_per_producer) precisa ser divisivel por n_consumers")

    buffer = BoundedBuffer(config.buffer_size, config.mode)
    total_items = config.total_items
    items_per_consumer = total_items // config.n_consumers

    collected: list = []
    collected_lock = threading.Lock()
    threads = []

    for i in range(config.n_producers):
        producer_start = i * config.items_per_producer + 1
        threads.append(
            threading.Thread(
                target=_producer,
                args=(buffer, producer_start, config.items_per_producer),
            )
        )

    for _ in range(config.n_consumers):
        threads.append(
            threading.Thread(
                target=_consumer,
                args=(buffer, items_per_consumer, collected, collected_lock),
            )
        )

    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Faixas dos produtores sao 1..total_items, disjuntas e contiguas:
    # o checksum produzido vem de formula fechada, nao de acumulacao
    # concorrente (docs/spec/plan.md, secao 4).
    produced_checksum = total_items * (total_items + 1) // 2

    unwritten_reads = sum(1 for value in collected if value is None)
    read_values = [value for value in collected if value is not None]
    consumed_checksum = sum(read_values)

    seen: set[int] = set()
    duplicated_reads = 0
    for value in read_values:
        if value in seen:
            duplicated_reads += 1
        else:
            seen.add(value)

    return ExperimentResult(
        mode=config.mode,
        produced_checksum=produced_checksum,
        consumed_checksum=consumed_checksum,
        duplicated_reads=duplicated_reads,
        unwritten_reads=unwritten_reads,
        elapsed_ms=elapsed_ms,
    )
