"""Testes deterministicos da API do BoundedBuffer, uma thread so.

Implementa ISSUE-006. Nao criam threads: nao provam nem derrubam a hipotese
de exclusao mutua (isso e papel da bateria em tests/battery.py), provam que
a estrutura de dados em si esta correta (docs/spec/spec.md, secao 6).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.buffer import BoundedBuffer, SyncMode

ALL_MODES = [SyncMode.NONE, SyncMode.COUNTING, SyncMode.FULL]


@pytest.mark.parametrize("mode", ALL_MODES)
def test_put_get_preserva_o_valor(mode):
    buffer = BoundedBuffer(capacity=4, mode=mode)
    buffer.put(42)
    assert buffer.get() == 42


@pytest.mark.parametrize("mode", ALL_MODES)
def test_ordem_de_retirada_e_fifo(mode):
    buffer = BoundedBuffer(capacity=4, mode=mode)
    for value in (10, 20, 30):
        buffer.put(value)

    assert [buffer.get(), buffer.get(), buffer.get()] == [10, 20, 30]


@pytest.mark.parametrize("mode", ALL_MODES)
def test_reaproveita_slots_ao_dar_a_volta(mode):
    capacity = 3
    buffer = BoundedBuffer(capacity=capacity, mode=mode)

    for volta in range(5):
        valores = [volta * 10 + i for i in range(capacity)]
        for valor in valores:
            buffer.put(valor)
        lidos = [buffer.get() for _ in range(capacity)]
        assert lidos == valores


def test_capacidade_invalida_levanta_erro():
    with pytest.raises(ValueError):
        BoundedBuffer(capacity=0, mode=SyncMode.FULL)
