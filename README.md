# data-ecosystem-gb-santander

This repository contains the analytical work for challenge:

- Gobernación de Santander - Smart web dashboard for citizen security in Santander.

The project follows a modular structure. Shared logic lives in a common core; challenge-specific logic lives in dedicated modules.

## Repository Structure
```bash
data-ecosystem-gb-santander/
├── src/
│   ├── core/               # Shared logic for both challenges
│   └── gb-santander/          # Challenge-specific code
├── scripts/                # ETLs, preprocessing, EDA runners, pipelines
├── data/
│   ├── raw/                # Unmodified datasets
│   └── processed/          # Cleaned / engineered datasets
├── sandbox/                # Personal workspaces
│       ├── eda.ipynb
│       ├── dari/
│       └── ...
│       # general notebooks can go directly under sandbox/
│       # example: sandbox/eda_xdataset.ipynb
└── .devcontainer/
```

## Environment Variables

```.devcontainer/.env```

This file will hold any credentials, paths, or configuration required for local execution inside the devcontainer.

## Development Guidelines

- Shared logic → src/core/
- Challenge-specific logic → src/gb-santander/
- Scripts (ETL, EDA, preprocessing, pipelines) → scripts/
- Notebooks → sandbox/<name>/ or in sandbox/ for general work
- Data → data/raw/ and data/processed/
- No credentials outside .devcontainer/.env

## Using the Devcontainer

1. Install the Dev Containers extension in VS Code.
2. Open the command palette (Ctrl + Shift + P) and select: ```Dev Containers: Reopen in Container```

This will start the environment defined in .devcontainer/.
