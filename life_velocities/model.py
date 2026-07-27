from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import z3

from .quotient import StripQuotient


@dataclass(frozen=True)
class SearchSpec:
    length: int
    width: int
    period: int = 10
    displacement: int = 6
    seam_phase: int = 0
    background_period: int = 1
    background_x_period: int = 4
    background_y_period: int = 4
    background_phase: int = 0
    guard_columns: int = 1
    require_live_background: bool = True
    require_motion: bool = True

    def validate(self) -> None:
        if self.length <= 2 * self.guard_columns:
            raise ValueError("length must exceed twice guard_columns")
        if min(
            self.background_period,
            self.background_x_period,
            self.background_y_period,
        ) <= 0:
            raise ValueError("background periods must be positive")
        if self.guard_columns < 1:
            raise ValueError("at least one guard column is required")


class WaveModel:
    def __init__(self, spec: SearchSpec) -> None:
        spec.validate()
        self.spec = spec
        self.quotient = StripQuotient(
            spec.period,
            spec.displacement,
            spec.length,
            spec.width,
            spec.seam_phase,
        )
        self.representatives = self.quotient.representatives()
        self.solver = z3.Solver()
        self.cells = {
            key: z3.Bool(f"q_{key[0]}_{key[1]}_{key[2]}")
            for key in self.representatives
        }
        self.background = {
            (t, x, y): z3.Bool(f"b_{t}_{x}_{y}")
            for t in range(spec.background_period)
            for x in range(spec.background_x_period)
            for y in range(spec.background_y_period)
        }
        self._add_life_rules()
        self._add_background_rules()
        self._add_support_constraints()

    @staticmethod
    def _life_rule(
        following: z3.BoolRef,
        current: z3.BoolRef,
        neighbors: list[z3.BoolRef],
    ) -> z3.BoolRef:
        count = z3.Sum([z3.If(value, 1, 0) for value in neighbors])
        return following == z3.Or(count == 3, z3.And(current, count == 2))

    def cell(self, t: int, x: int, y: int) -> z3.BoolRef:
        return self.cells[self.quotient.key(t, x, y)]

    def bg(self, t: int, x: int, y: int) -> z3.BoolRef:
        spec = self.spec
        return self.background[
            (
                t % spec.background_period,
                x % spec.background_x_period,
                y % spec.background_y_period,
            )
        ]

    def _add_life_rules(self) -> None:
        for t, x, y in self.representatives.values():
            neighbors = [
                self.cell(t, x + dx, y + dy)
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dx, dy) != (0, 0)
            ]
            self.solver.add(
                self._life_rule(
                    self.cell(t + 1, x, y),
                    self.cell(t, x, y),
                    neighbors,
                )
            )

    def _add_background_rules(self) -> None:
        spec = self.spec
        for t in range(spec.background_period):
            for x in range(spec.background_x_period):
                for y in range(spec.background_y_period):
                    neighbors = [
                        self.bg(t, x + dx, y + dy)
                        for dy in (-1, 0, 1)
                        for dx in (-1, 0, 1)
                        if (dx, dy) != (0, 0)
                    ]
                    self.solver.add(
                        self._life_rule(
                            self.bg(t + 1, x, y),
                            self.bg(t, x, y),
                            neighbors,
                        )
                    )

    def _add_support_constraints(self) -> None:
        spec = self.spec
        guard_x = list(range(spec.guard_columns)) + list(
            range(spec.length - spec.guard_columns, spec.length)
        )
        for t in range(spec.period):
            for x in guard_x:
                for y in range(spec.width):
                    self.solver.add(
                        self.cell(t, x, y)
                        == self.bg(t + spec.background_phase, x, y)
                    )

        differences = [
            self.cell(t, x, y) != self.bg(t + spec.background_phase, x, y)
            for t in range(spec.period)
            for x in range(spec.guard_columns, spec.length - spec.guard_columns)
            for y in range(spec.width)
        ]
        self.solver.add(z3.Or(differences))
        if spec.require_live_background:
            self.solver.add(z3.Or(list(self.background.values())))
        if spec.require_motion and spec.displacement:
            self.solver.add(
                z3.Or(
                    [
                        self.cell(0, x, y) != self.cell(spec.period, x, y)
                        for x in range(spec.length)
                        for y in range(spec.width)
                    ]
                )
            )

    def solve(self, timeout_ms: int | None = None) -> dict[str, Any]:
        if timeout_ms is not None:
            self.solver.set(timeout=timeout_ms)
        status = self.solver.check()
        result: dict[str, Any] = {
            "format": "life_velocities.wave.v1",
            "spec": asdict(self.spec),
            "quotient_index": self.quotient.index,
            "status": str(status),
        }
        if status == z3.sat:
            model = self.solver.model()
            result["live_cosets"] = [
                list(key)
                for key, variable in sorted(self.cells.items())
                if z3.is_true(model.eval(variable, model_completion=True))
            ]
            result["live_background"] = [
                list(key)
                for key, variable in sorted(self.background.items())
                if z3.is_true(model.eval(variable, model_completion=True))
            ]
        elif status == z3.unknown:
            result["reason_unknown"] = self.solver.reason_unknown()
        return result
