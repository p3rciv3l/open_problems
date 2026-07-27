from dataclasses import dataclass
from itertools import product

from .life import Cell, Pattern, serialize, step

Bounds = tuple[int, int, int, int]
Clause = tuple[int, ...]


def _inside(cell: Cell, bounds: Bounds) -> bool:
    x, y = cell
    xmin, xmax, ymin, ymax = bounds
    return xmin <= x <= xmax and ymin <= y <= ymax


class _CNF:
    def __init__(self) -> None:
        self.names: list[tuple[int, Cell] | None] = [None]
        self.variables: dict[tuple[int, Cell], int] = {}
        self.clauses: list[Clause] = []

    def variable(self, generation: int, cell: Cell) -> int:
        key = generation, cell
        if key not in self.variables:
            self.variables[key] = len(self.names)
            self.names.append(key)
        return self.variables[key]

    def fixed(self, variable: int, value: bool) -> None:
        self.clauses.append((variable if value else -variable,))


def _life_value(center: bool, neighbors: tuple[bool, ...]) -> bool:
    count = sum(neighbors)
    return count == 3 or (center and count == 2)


def _encode_life(cnf: _CNF, previous: list[int], output: int) -> None:
    for values in product((False, True), repeat=9):
        expected = _life_value(values[0], values[1:])
        clause = [
            -variable if value else variable
            for variable, value in zip(previous, values, strict=True)
        ]
        clause.append(output if expected else -output)
        cnf.clauses.append(tuple(clause))


def _solve(
    clauses: list[Clause], variable_count: int, branch_order: list[int]
) -> list[bool] | None:
    assignment: list[bool | None] = [None] * (variable_count + 1)

    def search() -> list[bool] | None:
        while True:
            unit: int | None = None
            for clause in clauses:
                unresolved: list[int] = []
                satisfied = False
                for literal in clause:
                    value = assignment[abs(literal)]
                    if value is None:
                        unresolved.append(literal)
                    elif value == (literal > 0):
                        satisfied = True
                        break
                if satisfied:
                    continue
                if not unresolved:
                    return None
                if len(unresolved) == 1:
                    unit = unresolved[0]
                    break
            if unit is None:
                break
            index = abs(unit)
            value = unit > 0
            if assignment[index] is not None and assignment[index] != value:
                return None
            assignment[index] = value

        variable = next(
            (index for index in branch_order if assignment[index] is None), None
        )
        if variable is None:
            return [bool(value) for value in assignment]
        snapshot = assignment.copy()
        for value in (False, True):
            assignment[variable] = value
            result = search()
            if result is not None:
                return result
            assignment[:] = snapshot
        return None

    return search()


@dataclass(frozen=True)
class BoundedResult:
    safe: bool
    horizon: int
    protected: Cell
    exterior_live: Pattern
    flip_generation: int | None
    trace: tuple[Pattern, ...]
    variables: int
    clauses: int

    def as_dict(self) -> dict[str, object]:
        return {
            "safe": self.safe,
            "horizon": self.horizon,
            "protected": list(self.protected),
            "exterior_live": serialize(self.exterior_live),
            "flip_generation": self.flip_generation,
            "trace": [serialize(pattern) for pattern in self.trace],
            "sat_variables": self.variables,
            "sat_clauses": self.clauses,
        }


def check_bounded_flip(
    target: Pattern,
    protected_region: Bounds,
    protected: Cell,
    horizon: int,
) -> BoundedResult:
    """Decide whether any initial exterior assignment flips protected by horizon.

    Every cell in protected_region is fixed alive/dead by target. All cells
    outside it in the protected cell's radius-horizon light cone are free SAT
    variables. Cells farther away are causally irrelevant to the query.
    """
    if horizon < 1:
        raise ValueError("horizon must be positive")
    if not _inside(protected, protected_region):
        raise ValueError("protected cell must lie in protected_region")
    if any(not _inside(cell, protected_region) for cell in target):
        raise ValueError("target must be contained in protected_region")

    cnf = _CNF()
    px, py = protected
    exterior_variables: list[int] = []
    for generation in range(horizon + 1):
        radius = horizon - generation
        for x in range(px - radius, px + radius + 1):
            for y in range(py - radius, py + radius + 1):
                cnf.variable(generation, (x, y))

    for cell in [
        (x, y)
        for x in range(px - horizon, px + horizon + 1)
        for y in range(py - horizon, py + horizon + 1)
    ]:
        variable = cnf.variable(0, cell)
        if _inside(cell, protected_region):
            cnf.fixed(variable, cell in target)
        else:
            exterior_variables.append(variable)

    for generation in range(1, horizon + 1):
        radius = horizon - generation
        for x in range(px - radius, px + radius + 1):
            for y in range(py - radius, py + radius + 1):
                inputs = [cnf.variable(generation - 1, (x, y))]
                inputs.extend(
                    cnf.variable(generation - 1, (x + dx, y + dy))
                    for dx in (-1, 0, 1)
                    for dy in (-1, 0, 1)
                    if (dx, dy) != (0, 0)
                )
                _encode_life(cnf, inputs, cnf.variable(generation, (x, y)))

    initially_alive = protected in target
    flip_literals = [
        -cnf.variable(generation, protected)
        if initially_alive
        else cnf.variable(generation, protected)
        for generation in range(1, horizon + 1)
    ]
    cnf.clauses.append(tuple(flip_literals))
    all_variables = list(range(1, len(cnf.names)))
    order = exterior_variables + [
        variable for variable in all_variables if variable not in exterior_variables
    ]
    model = _solve(cnf.clauses, len(cnf.names) - 1, order)

    if model is None:
        return BoundedResult(
            True,
            horizon,
            protected,
            frozenset(),
            None,
            tuple(),
            len(cnf.names) - 1,
            len(cnf.clauses),
        )

    exterior = frozenset(
        cnf.names[variable][1]  # type: ignore[index]
        for variable in exterior_variables
        if model[variable]
    )
    current = frozenset(target | exterior)
    trace = [current]
    flip_generation = None
    for generation in range(1, horizon + 1):
        current = step(current)
        trace.append(current)
        if flip_generation is None and ((protected in current) != initially_alive):
            flip_generation = generation
    if flip_generation is None:
        raise AssertionError("SAT model did not reproduce under sparse simulation")
    return BoundedResult(
        False,
        horizon,
        protected,
        exterior,
        flip_generation,
        tuple(trace),
        len(cnf.names) - 1,
        len(cnf.clauses),
    )
