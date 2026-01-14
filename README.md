# Hacker Crush

A cybersecurity-themed match-3 puzzle game inspired by Candy Crush, featuring a dark hacker aesthetic with Matrix-style visuals and moody atmospheric sound design.

![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Pygame](https://img.shields.io/badge/pygame-2.0+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)

## Features

### Gameplay
- **Match-3 mechanics** - Swap adjacent candies to create matches of 3 or more
- **Special candies** - Create powerful combos:
  - **Striped** (4-match) - Clears entire row or column
  - **Wrapped** (L/T-shape) - Explodes in a 3x3 area twice
  - **Color Bomb** (5-match) - Clears all candies of one type
- **Cascading combos** - Chain reactions multiply your score
- **Three game modes**:
  - Endless - Play until no moves remain
  - Moves - Reach target score within limited moves
  - Timed - Race against the clock

### Visuals
- Matrix-style falling code rain background
- CRT scanline overlay effect
- Particle effects for matches and special activations
- Hacker-themed candy sprites (blackhat, defcon, ronin, lock, key, virus)
- Security Ronin branding

### Audio
- Moody Matrix-inspired synthesized sound effects
- Dark, atmospheric, low-frequency design
- Reverb and filtering for cinematic feel

## Installation

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/hacker-crush.git
cd hacker-crush

# Install dependencies
pip install pygame numpy scipy

# Run the game
python src/main.py
```

## Controls

### Menu
- **Arrow Keys** - Navigate options
- **Enter** - Select
- **Mouse** - Click to select

### Gameplay
- **Click + Drag** - Swap candies
- **ESC** - Return to menu
- **Click Logo** - Visit Security Ronin website

## Project Structure

```
hacker-crush/
├── src/
│   ├── main.py          # Game loop and event handling
│   ├── board.py         # Game board logic
│   ├── candy.py         # Candy class and special types
│   ├── matcher.py       # Match detection algorithms
│   ├── renderer.py      # Pygame rendering with effects
│   ├── audio.py         # Sound effect management
│   ├── animations.py    # Swap and clear animations
│   ├── particles.py     # Particle effects system
│   └── constants.py     # Game configuration
├── assets/
│   ├── images/          # Candy sprites and logo
│   └── sounds/          # Synthesized sound effects
├── tests/               # Pytest test suite
├── scripts/
│   └── generate_sounds.py  # Sound synthesis script
└── README.md
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src
```

### Regenerating Sounds

The Matrix-style sound effects are procedurally generated:

```bash
python scripts/generate_sounds.py
```

## Tech Stack

- **Python 3.11+** - Core language
- **Pygame** - Game framework and rendering
- **NumPy** - Sound synthesis
- **SciPy** - Audio filtering and effects
- **Pytest** - Testing framework

## Credits

- Game concept inspired by Candy Crush Saga
- Developed by [Security Ronin](https://www.securityronin.com/)
- Matrix visual aesthetic inspired by The Matrix (1999)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
