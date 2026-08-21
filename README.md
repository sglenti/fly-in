Fly-in

This project has been created as part of the 42 curriculum by slenti.
Description

Fly-in is a custom-designed drone routing simulation system. The goal of this project is to navigate a fleet of drones from a central starting hub to a target destination through a dynamic network of zones, while respecting strict movement, occupancy, and capacity constraints. The project focuses on algorithmic efficiency, object-oriented design, and robust simulation logic.
Instructions
Prerequisites

    Python 3.10+
    pip or uv for dependency management

Installation

Clone the repository and install the required dependencies:
bash

make install

Running the simulation

To execute the simulation with a provided map file:
bash

make run map=path/to/your/map.txt

Testing & Linting

To run the static analysis (flake8 and mypy) to ensure code quality:
bash

make lint

Note: Use make lint-strict for a more rigorous check.
Implementation Strategy

    Architecture: The project follows an object-oriented paradigm. The system is split into three main modules:
        Models: Defines the data structures (Zone, Connection, Drone, Map).
        Parser: Handles the ingestion and validation of the input map files.
        Simulation Engine: Manages the turn-based logic, drone scheduling, and pathfinding.
    Algorithm: The core pathfinding is implemented using A* Search. It calculates paths based on weighted zone costs while dynamically resolving occupancy conflicts to prevent bottlenecks.

Visual Representation

The project provides visual feedback via colored terminal output. This allows users to track the status of zones and the movement of individual drones turn-by-turn.
Resources

    [List any official Python documentation or algorithm resources you used]
    AI Usage: This project utilized AI as a peer-programming partner to:
        Design the project architecture and class hierarchies.
        Explain concepts related to graph theory and multi-agent pathfinding.
        Review and refine the implementation of the simulation engine.

