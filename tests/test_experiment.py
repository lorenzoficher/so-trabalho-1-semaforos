"""Testes deterministicos da validacao de entrada de run_experiment.

Nao cobrem o fenomeno de concorrencia (isso e papel de tests/battery.py),
so os erros que run_experiment deve recusar antes de criar qualquer thread.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.buffer import SyncMode
from src.experiment import ExperimentConfig, run_experiment


def test_total_items_nao_divisivel_por_consumers_levanta_erro():
    config = ExperimentConfig(
        mode=SyncMode.FULL, n_producers=1, n_consumers=3, items_per_producer=2
    )
    with pytest.raises(ValueError):
        run_experiment(config)


@pytest.mark.parametrize("n_producers,n_consumers", [(0, 4), (4, 0), (-1, 4)])
def test_producers_ou_consumers_invalidos_levanta_erro(n_producers, n_consumers):
    config = ExperimentConfig(
        mode=SyncMode.FULL, n_producers=n_producers, n_consumers=n_consumers
    )
    with pytest.raises(ValueError):
        run_experiment(config)
