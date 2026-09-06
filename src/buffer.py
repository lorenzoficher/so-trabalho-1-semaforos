"""Buffer circular limitado, compartilhado por produtores e consumidores.

Implementa ISSUE-001 (docs/issues/ISSUE-001-buffer-e-modos-de-sincronizacao.md).
"""

from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Any, Optional


class SyncMode(Enum):
    """Qual conjunto de semaforos esta ativo em uma execucao."""

    NONE = "none"
    COUNTING = "counting"
    FULL = "full"


class BoundedBuffer:
    """Buffer circular de capacidade fixa.

    O modo controla quais semaforos existem:

    - NONE: nenhum semaforo. put/get acessam os indices e os slots direto.
    - COUNTING: semaforos contadores `empty`/`full` (capacidade), sem mutex.
    - FULL: `empty`/`full` mais um semaforo binario `mutex` (exclusao mutua).
    """

    def __init__(self, capacity: int, mode: SyncMode) -> None:
        if capacity <= 0:
            raise ValueError("capacity precisa ser positiva")

        self._capacity = capacity
        self._mode = mode
        self._slots: list[Optional[Any]] = [None] * capacity
        self._write_index = 0
        self._read_index = 0

        if mode in (SyncMode.COUNTING, SyncMode.FULL):
            self._empty: Optional[threading.Semaphore] = threading.Semaphore(capacity)
            self._full: Optional[threading.Semaphore] = threading.Semaphore(0)
        else:
            self._empty = None
            self._full = None

        self._mutex: Optional[threading.Semaphore] = (
            threading.Semaphore(1) if mode is SyncMode.FULL else None
        )

    def put(self, item: Any) -> None:
        if self._empty is not None:
            self._empty.acquire()
        if self._mutex is not None:
            self._mutex.acquire()

        # Secao critica: ler o indice, calcular o slot e gravar nao e uma
        # operacao atomica. So o modo FULL protege este trecho com _mutex.
        # O sleep(0) so cede a GIL (nao dorme de fato); ele existe para
        # tornar a janela da corrida observavel de forma confiavel entre
        # maquinas, em vez de depender da sorte do agendador (docs/adr/0001).
        index = self._write_index % self._capacity
        time.sleep(0)
        self._slots[index] = item
        self._write_index += 1

        if self._mutex is not None:
            self._mutex.release()
        if self._full is not None:
            self._full.release()

    def get(self) -> Any:
        if self._full is not None:
            self._full.acquire()
        if self._mutex is not None:
            self._mutex.acquire()

        # Mesma secao critica de put(), do lado da leitura.
        index = self._read_index % self._capacity
        time.sleep(0)
        item = self._slots[index]
        self._read_index += 1

        if self._mutex is not None:
            self._mutex.release()
        if self._empty is not None:
            self._empty.release()

        return item
