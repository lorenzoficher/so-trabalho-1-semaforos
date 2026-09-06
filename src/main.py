"""CLI: roda uma execucao do experimento e imprime uma linha de resultado.

Implementa ISSUE-003. Exemplo:

    python -m src.main --mode full
    python -m src.main --mode none
    python -m src.main --mode counting --items-per-producer 5000
"""

from __future__ import annotations

import argparse

from src.buffer import SyncMode
from src.experiment import ExperimentConfig, run_experiment


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Experimento produtor-consumidor com semaforos.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=[mode.value for mode in SyncMode],
        help="Modo de sincronizacao.",
    )
    parser.add_argument("--buffer-size", type=int, default=10)
    parser.add_argument("--producers", type=int, default=4)
    parser.add_argument("--consumers", type=int, default=4)
    parser.add_argument("--items-per-producer", type=int, default=2500)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = ExperimentConfig(
        mode=SyncMode(args.mode),
        buffer_size=args.buffer_size,
        n_producers=args.producers,
        n_consumers=args.consumers,
        items_per_producer=args.items_per_producer,
    )
    result = run_experiment(config)

    print(
        f"modo={result.mode.value} "
        f"produzido={result.produced_checksum} "
        f"consumido={result.consumed_checksum} "
        f"diferenca={result.difference} "
        f"duplicados={result.duplicated_reads} "
        f"nao_escritos={result.unwritten_reads} "
        f"tempo_ms={result.elapsed_ms:.3f}"
    )


if __name__ == "__main__":
    main()
