# Fly-in

*This project has been created as part of the 42 curriculum by slenti.*

## Description 
**Fly-in** is an autonomous drone routing simulation system designed to navigate a fleet of drones through a complex, weighted network of connected zones. The project focuses on optimizing throughput, minimizing simulation turns, and handling strict spatial and temporal constraints (such as zone capacities, link bandwidth limits, multi-turn restricted zones, and priority routing). 

At its core, the system utilizes a custom **3D Space-Time Dijkstra pathfinding algorithm** combined with a global capacity-aware reservation table to pre-compute collision-free trajectories. It features a decoupled architecture separating the core simulation engine from both a real-time Pygame graphical visualizer and a custom Rich Terminal User Interface (TUI) dashboard.
 
 
## Architecture & Algorithm Design

The project includes:
- A parser for the map file.
- A simulation engine that advances drones in discrete turns and enforces:
  - zone occupancy (max_drones),
  - connection capacity (max_link_capacity),
  - multi-turn movements for restricted zones.
- A time-aware pathfinder that schedules routes while accounting for
  reservations and optional heuristics.
- Visual output:
  - colored terminal dashboard (Rich) and
  - graphical window animation (Pygame).

High-level architecture:
- `src/models/` — Pydantic models: Zone, ZoneMetadata, Connection, Drone, Map
- `src/parser.py` — robust parser that validates syntax, coordinates, and metadata
- `src/simulation/engine.py` — orchestrates turns, validates moves, and updates drones
- `src/simulation/pathfinder.py` — time-aware pathfinder
- `src/view/` — `ConsoleRenderer` (Rich) and `WindowRenderer` (Pygame)

### 1. Data Layer & Validation
- **Pydantic Models (`src/models/`):** `Zone`, `Connection`, and `Drone` enforce strict invariants at instantiation (e.g., forbidding dashes in zone names via custom field validators, ensuring positive coordinate bounds, and making edges hashable via `frozen=True`).
- **Graph Registry (`Map`):** Acts as the single source of truth, organizing zones into an $O(1)$ lookup registry and pre-indexing an adjacency list (`_adj_list`) for rapid graph traversal.

### 2. The Pathfinder (3D Space-Time Dijkstra)
Instead of handling collisions dynamically at runtime, the pathfinder evaluates paths across a 3D coordinate space: `(x, y, time)`.
- **Temporal Reservations:** Tracks spatial-temporal occupancy using a capacity-aware dictionary `{(node, time): count}` and link usage `{(connection, time): count}`.
- **Prioritized Planning:** Routes drones sequentially. Each drone builds its path while respecting the cumulative temporal footprints of all preceding drones, naturally resolving bottlenecks and forcing vehicles to wait or take parallel alternate routes.
- **Tie-Breaker Optimization:** Implements a custom negative priority counter in the min-heap tuple `(cost, -priority_count, node, time)` to deterministically favor preferred zones during cost ties.

### 3. Decoupled Rendering Pipeline (`src/view/`)
- **Headless Engine:** The simulation core (`SimulationEngine`) is entirely decoupled from the UI, running purely as a state machine that can operate headlessly for testing or automated evaluation scripts.
- **Pygame Visualizer:** Renders the map topology and translates discrete turn states into smooth 60 FPS animations using Linear Interpolation (Lerp), abstract procedural drones, and docked positions for multiple drones in the same hub.
- **Rich TUI Dashboard:** A top-anchored layout featuring a real-time telemetry table with dynamic column sizing, terminal-width responsiveness, and a scrolling per-turn movements log. Additionally presenting some final figures summarizing the simulation execution before exiting. 

#### Complexity:
- Worst-case state-space search can blow up if time horizon is large (search over `(node, time)` states).
- Heuristic (when enabled) helps prune search and reduce exploration.
- The implementation caches reservations per planning round but does not persist full path caches across major topology changes (the code lays a foundation for caching and incremental updates).

#### Design trade-offs:
- This design favors correctness and constraint enforcement; for very large numbers of drones or long horizons, further optimizations (incremental replanning, hierarchical routing, or prioritized planning) can help scale.

## Instructions & Installation

### Prerequisites
Ensure you have `Python 3.10+` and `uv` installed on your system.

### 1. Installation
Clone the repository and install dependencies using the provided Makefile:
```bash
git clone https://github.com/sglenti/fly-in.git
cd fly-in
make install
```

### 2. Makefile targets
The Makefile provides convenient commands: 

- `make install` — install project dependencies
- `make run map=path/to/map.txt` — run the simulation with the specified map file
- `make debug map=path/to/map.txt` — run under pdb for debugging
- `make clean` — remove caches and temporary files (e.g., __pycache__, .mypy_cache)
- `make lint` — run `flake8 .` and `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`
- `make lint-strict` — run `flake8 .` and `mypy . --strict` (stricter type checking)

To run the project with a specific map file, use the run rule:
```bash

make run map=maps/hard/01_ultimate_challenge.txt
```

### 3. Running the Simulation

Besides the run target included in the Makefile, the simulation can be run directly via **uv run**, specifying the map file
and optional arguments:

```bash 
uv run src maps/hard/01_ultimate_challenge.txt
```
Run with interactive, step-by-step mode 
```bash 
uv run src --interactive maps/hard/01_ultimate_challenge.txt
```
Run with heuristics enabled (A*-like behaviour)

```bash 
uv run src --heuristics maps/hard/01_ultimate_challenge.txt
```
#### Keyboard Input
- Press **’q’** or **’Esc’** to exit the simulation.
- In interactive mode, press **’n’** to advance the turn.
 
## Map file format

The input file format follows strict rules. Minimal example:

```
nb_drones: 3
start_hub: base 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: A 2 1 [zone=priority color=blue max_drones=2]
hub: B 4 3 [zone=restricted]
connection: base-A
connection: A-B [max_link_capacity=2]
connection: B-goal
```

General Notes:
- First line must be `nb_drones: <positive_integer>`.
- Zone lines format: `start_hub: name x y [metadata]`, `end_hub: ...`, `hub: ...`.
- Connection lines format: `connection: name1-name2 [max_link_capacity=<N>]`.
- Names must not contain dashes or spaces.
- Comments start with ’#’ and are ignored.

### Zones
Zones are defined one per line using type prefixes: 
```
start_hub: <name> <x> <y> [metadata]
end_hub: <name> <x> <y> [metadata]
hub: <name> <x> <y> [metadata] 
```
The zones coordinates will always be integers, and there will always
be a unique start and a unique end zone. 
The connection syntax forbids dashes in zone names. 

#### Zone Metadata
All metadata is optional and enclosed in brackets [...] with default values:
- zone=<type> (default: normal) 
- color=<value> (default: none) 
- max_drones=<number> (default: 1) - Maximum drones that can occupy this
zone simultaneously 
- Tags inside brackets can appear in any order. 
 
#### Zone types 
- normal – Standard zone with 1 turn movement cost (default) 
- blocked – Inaccessible zone. Drones must not enter or pass through this zone. 
Any path using it is invalid. 
- restricted – A sensitive or dangerous zone. Movement to this zone costs 2
turns. 
- priority – A preferred zone. Movement to this zone costs 1 turn but should
be prioritized in pathfinding. 
 
#### Zone Color: 
colors are optional and are used for visual representation.
Accepted values for color are any valid single-word strings (e.g., red, blue,
gray). There is no fixed list of allowed colors.

### Connections
Connections are defined one per line using the prefix **connection**:
```
connection: <name1>-<name2> [metadata]
```
- **name1** and **name1** are previously defined zone names and must be separated by a single dash ’-’
- Define a bidirectional connection (edge) between two zones.
- Optional metadata can be specified in brackets [...]:

#### Connection Metadata:
- max_link_capacity=<number> (default: 1) 
Maximum drones that can traverse this connection simultaneously 

## Expected output format

Each simulation turn is one output line listing movements that occurred during
that turn (space-separated). Movement tokens follow these formats:

- `D<ID>-<zone>` for a drone arriving at `zone`
- `D<ID>-<a>-<b>` (or `D<ID>-<connection>`) for a drone in transit between zones (restricted movement consumes 2 turns)

Example:
```
D1-A D2-B
D1-goal D2-goal
```

Drones that do not move on a given turn are omitted on that line. The simulation
ends when all drones have reached the end hub. 

## Resources
 - 
 - Pygame Documentation: https://www.pygame.org/docs/
 - Rich Documentation: https://rich.readthedocs.io/en/stable/index.html
 - Pydantic: https://pydantic.dev/docs/validation/latest/get-started/

## AI Usage Disclosure

During the development of this project, AI tools were utilized for:

    Architectural Brainstorming: Discussing trade-offs between distributed vs. centralized graph registries and designing the 3D space-time state machine.
    Debugging Assistance: Resolving subtle Pydantic V2 configuration conflicts and optimizing heap queue tie-breakers.
    TUI Layout Structuring: Designing the top-anchored layout structure and auto-scrolling log streams using rich.
    Documentation drafting: propose and generate PEP-257 docstrings and simple README base.

All AI-generated snippets, algorithms, and architectural patterns were reviewed, understood, refactored, and integrated manually.
