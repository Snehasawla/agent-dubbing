# Debugging Agents Research Project

A comprehensive analysis project for debugging agents research, based on synthetic thesis data and academic paper metadata.

## Project Overview

This project analyzes debugging agents research through:
- Synthetic thesis section analysis
- Academic paper metadata exploration
- Research metrics and trends visualization
- Automated thesis structure analysis

## Project Structure

```
debugging_agents_project/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── data/                              # Data files
│   ├── debugging_agents_synthetic_annotations.csv
│   └── synthetic_pdf_papers_dataset.csv
├── notebooks/                         # Jupyter notebooks
│   ├── thesis_analysis.ipynb
│   └── paper_metadata_analysis.ipynb
├── src/                              # Source code
│   ├── data_processor.py
│   ├── visualizer.py
│   └── thesis_analyzer.py
├── reports/                          # Generated reports
│   ├── thesis_structure_analysis.html
│   └── research_trends_report.html
└── docs/                            # Documentation
    ├── methodology.md
    └── findings.md
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the main analysis:
```bash
python src/thesis_analyzer.py
```

3. Open Jupyter notebooks for interactive analysis:
```bash
jupyter notebook notebooks/
```

## Key Features

- **Thesis Structure Analysis**: Analyze section priorities, difficulty scores, and extraction metrics
- **Research Trends**: Visualize academic paper trends by domain, year, and metrics
- **Automated Reporting**: Generate HTML reports with visualizations
- **Interactive Exploration**: Jupyter notebooks for deep-dive analysis

## Data Sources

- `debugging_agents_synthetic_annotations.csv`: Section-level thesis data with 24 sections
- `synthetic_pdf_papers_dataset.csv`: 40 synthetic academic papers with metadata

## Methodology

The project uses data science techniques to:
1. Analyze thesis structure and content distribution
2. Identify high-priority sections for extraction
3. Visualize research trends across domains
4. Generate insights for debugging agents research

## Outputs

- Interactive visualizations
- Automated HTML reports
- Statistical analysis results
- Research recommendations
