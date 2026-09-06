"""Bateria de execucoes: roda o experimento N vezes por modo e agrega.

Implementa ISSUE-005. Uso:

    python tests/battery.py
    python tests/battery.py --repeticoes 50

Grava cada execucao individual em results/battery_results.csv e imprime um
resumo por modo (quantas corretas, quantas divergentes, tempo medio/min/max).
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.buffer import SyncMode
from src.experiment import ExperimentConfig, run_experiment


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bateria de execucoes do experimento.")
    parser.add_argument("--repeticoes", type=int, default=30)
    parser.add_argument("--buffer-size", type=int, default=10)
    parser.add_argument("--producers", type=int, default=4)
    parser.add_argument("--consumers", type=int, default=4)
    parser.add_argument("--items-per-producer", type=int, default=2500)
    parser.add_argument(
        "--saida",
        type=Path,
        default=PROJECT_ROOT / "results" / "battery_results.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.repeticoes < 1:
        raise SystemExit("--repeticoes precisa ser >= 1")
    args.saida.parent.mkdir(parents=True, exist_ok=True)

    linhas = []
    resumo = {}

    for mode in (SyncMode.NONE, SyncMode.COUNTING, SyncMode.FULL):
        tempos = []
        corretas = 0
        divergentes = 0

        for repeticao in range(1, args.repeticoes + 1):
            config = ExperimentConfig(
                mode=mode,
                buffer_size=args.buffer_size,
                n_producers=args.producers,
                n_consumers=args.consumers,
                items_per_producer=args.items_per_producer,
            )
            resultado = run_experiment(config)

            if resultado.is_correct:
                corretas += 1
            else:
                divergentes += 1
            tempos.append(resultado.elapsed_ms)

            linhas.append(
                {
                    "modo": mode.value,
                    "repeticao": repeticao,
                    "checksum_produzido": resultado.produced_checksum,
                    "checksum_consumido": resultado.consumed_checksum,
                    "diferenca": resultado.difference,
                    "duplicados": resultado.duplicated_reads,
                    "nao_escritos": resultado.unwritten_reads,
                    "tempo_ms": round(resultado.elapsed_ms, 3),
                }
            )

        resumo[mode.value] = {
            "corretas": corretas,
            "divergentes": divergentes,
            "tempo_medio_ms": statistics.mean(tempos),
            "tempo_min_ms": min(tempos),
            "tempo_max_ms": max(tempos),
        }

    with open(args.saida, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"{args.repeticoes} repeticoes por modo, resultados em {args.saida}\n")
    print(f"{'modo':<10}{'corretas':>10}{'divergentes':>13}{'tempo_medio_ms':>16}{'tempo_min_ms':>14}{'tempo_max_ms':>14}")
    for modo, dados in resumo.items():
        print(
            f"{modo:<10}"
            f"{dados['corretas']:>10}"
            f"{dados['divergentes']:>13}"
            f"{dados['tempo_medio_ms']:>16.3f}"
            f"{dados['tempo_min_ms']:>14.3f}"
            f"{dados['tempo_max_ms']:>14.3f}"
        )


if __name__ == "__main__":
    main()
