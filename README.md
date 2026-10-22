# sa_labs

Лабораторні роботи з системного аналізу.

## Структура

- `lab1/` — Практична робота №1. Аналіз предметної області (читає `system.json`, будує граф зв'язків, формує звіт).
- `lab2/` — Практична робота №2. Побудова моделі системи (мережева модель процесу, метод Сааті, математична модель навантаження).
- `lab3/` — Практична робота №3. Автоматизоване формування технічної специфікації (з `spec_input.json` у `technical_specification.md`).

## lab1: запуск

```bash
cd lab1
python3 -m venv venv
source venv/bin/activate      # zsh/bash
pip install -r requirements.txt
python system_analysis.py
```

Результат: `report.txt` (текстовий звіт) та `system_graph.png` (граф системи).

## lab2: запуск

```bash
cd lab2
python3 -m venv venv
source venv/bin/activate      # zsh/bash
pip install -r requirements.txt
python model_analysis.py
```

Результат: `report.txt`, `process_network.png`, `saaty_weights.png`, `module_load.png`.

## lab3: запуск

```bash
cd lab3
python3 spec_generator.py
```

Залежностей немає (лише стандартна бібліотека) — venv не потрібен.
Результат: `report.txt` та `technical_specification.md`.
