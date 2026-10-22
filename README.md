# sa_labs

Лабораторні роботи з системного аналізу.

## Структура

- `lab1/` — Практична робота №1. Аналіз предметної області (читає `system.json`, будує граф зв'язків, формує звіт).
- `lab2/` — TBD
- `lab3/` — TBD

## lab1: запуск

```bash
cd lab1
python3 -m venv venv
source venv/bin/activate      # zsh/bash
pip install -r requirements.txt
python system_analysis.py
```

Результат: `report.txt` (текстовий звіт) та `system_graph.png` (граф системи).
