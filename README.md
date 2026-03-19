*This project has been created as part of the 42 curriculum by ybel-maa, mgarcia2*

<h1 align="center">🧩 A-Maze-ing</h1>

<p align="center">
  <b>Maze generator in Python with multiple algorithms, visualization and pathfinding</b><br>
  <i>Because a labyrinth is not a place to be lost, but a path to be found.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg">
  <img src="https://img.shields.io/badge/status-in%20progress-orange">
  <img src="https://img.shields.io/badge/42-project-black">
</p>

---

## 🚀 Overview

**A-Maze-ing** is a Python project that generates fully valid mazes from a configuration file.
It combines **algorithms, graph theory, and clean architecture** to build, visualize, and solve mazes.

✨ This project is not just about generating mazes — it's about:

* Structuring complex logic
* Designing reusable systems
* Working efficiently in a team

---

## ⚙️ Features

* 🧠 Multiple generation algorithms:

  * Recursive Backtracking
  * Prim
  * Kruskal
* 🎨 ASCII visualization in terminal
* 🎬 Animated maze generation *(bonus)*
* 🧭 Shortest path solving (BFS)
* 📄 Configurable input file
* ♻️ Reusable module (`mazegen`)

---

## 🧪 Example

```
█████████████████████
█ S       █         █
█ ███████ █ █████ █ █
█     █   █     █ █ █
█████ █ ███████ █ █ █
█     █         █   █
█ █████████████████ █
█               E   █
█████████████████████
```

---

## 📦 Installation

```bash
git clone https://github.com/your-username/a-maze-ing.git
cd a-maze-ing
make install
```

---

## ▶️ Usage

```bash
make run
```

Or manually:

```bash
python3 a_maze_ing.py config/default.txt
```

---

## 🧾 Configuration File

Example:

```
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
ALGORITHM=backtracking
SEED=42
```

---

## 🧠 Algorithms

We implemented different maze generation strategies:

| Algorithm    | Characteristics                    |
| ------------ | ---------------------------------- |
| Backtracking | Fast, clean, classic               |
| Prim         | More random, organic shapes        |
| Kruskal      | Graph-based, structured generation |

👉 This allows flexibility and comparison between approaches.

---

## 🏗️ Architecture

```
maze/
├── generator.py
├── solver.py
├── model.py
├── algorithms/
```

* Separation of concerns
* Modular design
* Reusable components

---

## ♻️ Reusable Module

The project includes a reusable package:

```
mazegen/
```

You can:

* Generate mazes programmatically
* Customize parameters
* Retrieve paths and structure

---

## 🤝 Team Work

### 👤 ybel-maa

* Maze generation logic
* Algorithms implementation
* Pathfinding system

### 👤 mgarcia2

* Config parser
* Output system
* Visualization & animation

---

## 🛠️ Development

```bash
make lint
make debug
make clean
```

---

## 🤖 AI Usage

AI was used to:

* Structure the project
* Explore algorithm approaches
* Improve documentation

All generated content was reviewed and fully understood before use.

---

## 📚 Resources

* Python Documentation
* Graph Theory Basics
* Maze Generation Algorithms
* BFS / DFS concepts

---

## 🧠 Final Thoughts

This project represents a mix of:

* Logic
* Creativity
* Teamwork

> *"Simple problems don’t build strong developers — complex ones do."*
