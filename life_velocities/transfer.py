from __future__ import annotations

import hashlib
import itertools
import json
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Background:
    name: str
    x_period: int
    y_period: int
    temporal_period: int
    live: frozenset[tuple[int, int]]

    @classmethod
    def load(cls, path: Path) -> "Background":
        data = json.loads(path.read_text())
        if data["temporal_period"] != 1:
            raise ValueError("the current transfer implementation requires a static background")
        return cls(
            name=data["name"],
            x_period=data["x_period"],
            y_period=data["y_period"],
            temporal_period=data["temporal_period"],
            live=frozenset(tuple(cell) for cell in data["live"]),
        )

    def alive(self, x: int, y: int) -> bool:
        return (x % self.x_period, y % self.y_period) in self.live

    def validate_life(self) -> None:
        for x in range(self.x_period):
            for y in range(self.y_period):
                count = sum(
                    self.alive(x + dx, y + dy)
                    for dx in (-1, 0, 1)
                    for dy in (-1, 0, 1)
                    if (dx, dy) != (0, 0)
                )
                following = count == 3 or (self.alive(x, y) and count == 2)
                if following != self.alive(x, y):
                    raise ValueError(f"background is not static Life at {(x, y)}")


@dataclass(frozen=True)
class TransferSpec:
    period: int = 10
    displacement: int = 6
    width: int = 4
    max_column_deviations: int = 1
    background_phase: int = 0

    def validate(self, background: Background) -> None:
        if self.period <= 0 or self.displacement <= 0 or self.width <= 0:
            raise ValueError("period, displacement, and width must be positive")
        if self.max_column_deviations < 0:
            raise ValueError("max_column_deviations must be nonnegative")
        if self.width % background.y_period:
            raise ValueError("width must be a multiple of the background y period")
        if self.displacement % background.x_period:
            raise ValueError(
                "static background x period must divide the displacement"
            )


BoundaryState = tuple[int, tuple[int, ...]]


class TransferSearch:
    """Exact reachable graph for bounded-deviation spacetime columns.

    A column is the ``period * width`` bits C(t, x, y).  A boundary retains
    columns x-displacement through x.  Appending x+1 decides every Life rule
    centered at x, including C(period,x,y)=C(0,x-displacement,y).
    """

    def __init__(self, spec: TransferSpec, background: Background) -> None:
        spec.validate(background)
        background.validate_life()
        self.spec = spec
        self.background = background
        self._candidate_cache: dict[int, tuple[int, ...]] = {}
        self._validate_background_symmetry()

    @property
    def column_bits(self) -> int:
        return self.spec.period * self.spec.width

    @property
    def memory(self) -> int:
        return self.spec.displacement + 1

    def _bit(self, column: int, t: int, y: int) -> bool:
        index = (t % self.spec.period) * self.spec.width + y % self.spec.width
        return bool(column & (1 << index))

    def background_column(self, x: int) -> int:
        mask = 0
        for t in range(self.spec.period):
            for y in range(self.spec.width):
                if self.background.alive(x + self.spec.background_phase, y):
                    mask |= 1 << (t * self.spec.width + y)
        return mask

    def candidates(self, phase: int) -> tuple[int, ...]:
        phase %= self.background.x_period
        if phase not in self._candidate_cache:
            base = self.background_column(phase)
            values = []
            for count in range(self.spec.max_column_deviations + 1):
                for changed in itertools.combinations(range(self.column_bits), count):
                    mask = base
                    for index in changed:
                        mask ^= 1 << index
                    values.append(mask)
            self._candidate_cache[phase] = tuple(sorted(values))
        return self._candidate_cache[phase]

    def background_state(self, phase: int) -> BoundaryState:
        columns = tuple(
            self.background_column(x)
            for x in range(phase - self.spec.displacement, phase + 1)
        )
        return phase % self.background.x_period, columns

    def valid_extension(self, state: BoundaryState, following: int) -> bool:
        _, columns = state
        center = columns[-1]
        previous = columns[-2]
        wrapped_following = columns[0]
        for t in range(self.spec.period):
            for y in range(self.spec.width):
                neighbors = 0
                for dx, column in ((-1, previous), (0, center), (1, following)):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        neighbors += self._bit(column, t, y + dy)
                current = self._bit(center, t, y)
                next_alive = (
                    self._bit(center, t + 1, y)
                    if t + 1 < self.spec.period
                    else self._bit(wrapped_following, 0, y)
                )
                expected = neighbors == 3 or (current and neighbors == 2)
                if next_alive != expected:
                    return False
        return True

    def extensions(self, state: BoundaryState) -> Iterable[BoundaryState]:
        phase, columns = state
        next_phase = (phase + 1) % self.background.x_period
        for following in self.candidates(next_phase):
            if self.valid_extension(state, following):
                yield next_phase, columns[1:] + (following,)

    def is_background_state(self, state: BoundaryState) -> bool:
        return state == self.background_state(state[0])

    @staticmethod
    def _encode_state(state: BoundaryState) -> bytes:
        phase, columns = state
        return f"{phase}:{','.join(format(value, 'x') for value in columns)}".encode()

    def search(self) -> dict[str, object]:
        start = self.background_state(0)
        queue = deque([start])
        predecessor: dict[BoundaryState, BoundaryState | None] = {start: None}
        graph_hash = hashlib.sha256()
        edges = 0

        while queue:
            state = queue.popleft()
            targets = sorted(self.extensions(state), key=self._encode_state)
            for target in targets:
                edges += 1
                graph_hash.update(self._encode_state(state))
                graph_hash.update(b"->")
                graph_hash.update(self._encode_state(target))
                graph_hash.update(b"\n")
                if self.is_background_state(target) and not self.is_background_state(state):
                    path = [target]
                    cursor: BoundaryState | None = state
                    while cursor is not None:
                        path.append(cursor)
                        cursor = predecessor[cursor]
                    path.reverse()
                    return self._result(
                        "witness",
                        len(predecessor),
                        edges,
                        graph_hash.hexdigest(),
                        path,
                    )
                if target not in predecessor:
                    predecessor[target] = state
                    queue.append(target)

        return self._result(
            "absent",
            len(predecessor),
            edges,
            graph_hash.hexdigest(),
            None,
        )

    def _result(
        self,
        status: str,
        states: int,
        edges: int,
        graph_sha256: str,
        path: list[BoundaryState] | None,
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "format": "life_velocities.isolated_transfer.v1",
            "status": status,
            "spec": asdict(self.spec),
            "background": {
                "name": self.background.name,
                "x_period": self.background.x_period,
                "y_period": self.background.y_period,
                "temporal_period": self.background.temporal_period,
                "live": sorted(map(list, self.background.live)),
            },
            "state_class": {
                "column_bits": self.column_bits,
                "boundary_columns": self.memory,
                "maximum_deviations_per_column": self.spec.max_column_deviations,
                "candidate_columns_per_phase": len(self.candidates(0)),
            },
            "reachable_states": states,
            "reachable_edges": edges,
            "ordered_graph_sha256": graph_sha256,
        }
        if path is not None:
            result["path"] = [
                {"phase": phase, "columns_hex": [format(value, "x") for value in columns]}
                for phase, columns in path
            ]
        return result

    def _validate_background_symmetry(self) -> None:
        for x in range(self.background.x_period):
            state = self.background_state(x)
            following = self.background_column(x + 1)
            if not self.valid_extension(state, following):
                raise ValueError(
                    "background does not obey Life plus the period/displacement relation"
                )
