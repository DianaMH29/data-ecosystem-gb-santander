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

## Project Resources
### Web Access
The dashboard developed for the Gobernación de Santander (Atlas del Crimen) is available for online access at the following link:

* http://gobsantander.eastus.cloudapp.azure.com:3001/
  
This instance provides interactive exploration of the processed datasets, security indicators, analytical modules, geospatial visualizations and chatbot built during the project.

### Demonstration Videos

The following videos present the functioning of the smart dashboard and chatbot for citizen security in Santander:
 * https://drive.google.com/file/d/1h3JFUxCmpidWlRI0xI7MDknqaoGgYOw2/view?usp=sharing
 * https://drive.google.com/file/d/1bMXhV5TvcFm94MuGir68p_vucneGOwwe/view?usp=sharing

### Project Presentation (Slides)

The official presentation used to explain the project, its architecture, methodology, and results:

* https://drive.google.com/file/d/1v492Ek8uKr-OG6YcFBl1IR_OqXGKgaG4/view?usp=sharing

Publication on Datos Abiertos de Colombia

The project is published on the official open data platform of Colombia.
* https://herramientas.datos.gov.co/usos/atlas-del-crimen
