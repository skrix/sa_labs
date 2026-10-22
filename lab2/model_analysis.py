"""
Системний аналіз. Практична робота №2.
Побудова моделі інформаційної системи та застосування методів моделювання.

Програма:
  1) читає структуру системи з ПР1 (system.json) і процес (process.json);
  2) будує мережеву модель процесу і рахує його час (критичний шлях);
  3) визначає важливість модулів методом аналізу ієрархій Т. Сааті;
  4) рахує добове навантаження модулів (математична модель);
  5) визначає проблемний модуль, формує рекомендації, графіки та звіт.
"""
import json

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# ---------------------------------------------------------------------------
# Вхідні дані методу Сааті: наскільки модуль важливіший для бізнес-цілі BO-1
# (заповнення звільнених слотів). Шкала 1–9, експерт — бізнес-аналітик.
SAATY_MODULES = ["Лист очікування", "Розклад", "Сповіщення",
                 "Онлайн-запис", "Особистий кабінет", "Звіти"]
SAATY_MATRIX = [
    # ЛО   Розк  Спов  Запис  Каб   Звіти
    [1,    2,    2,    3,     4,    6],    # Лист очікування
    [1/2,  1,    1,    2,     3,    5],    # Розклад
    [1/2,  1,    1,    2,     3,    5],    # Сповіщення
    [1/3,  1/2,  1/2,  1,     2,    4],    # Онлайн-запис
    [1/4,  1/3,  1/3,  1/2,   1,    2],    # Особистий кабінет
    [1/6,  1/5,  1/5,  1/4,   1/2,  1],    # Звіти
]
# Випадковий індекс узгодженості для матриць розміром n (таблиця Сааті)
RANDOM_INDEX = {3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}

# Вхідні дані математичної моделі (припущення)
LOCATIONS = 3                 # локацій салону
BOOKINGS_PER_DAY = 70         # записів на добу
CANCELLATIONS_PER_DAY = 10    # 15% записів скасовують
SEARCHES_PER_BOOKING = 4      # клієнт переглядає кілька днів перед записом
QUERY_TIME_MS = 80            # один запит до Розкладу по одній локації
OVERHEAD_MS = 40              # обробка запиту поза Розкладом
SEARCH_LIMIT_MS = 300         # вимога NFR-01
WAITLIST_REQUESTS_PER_DAY = 15  # нові заявки в лист очікування
STAFF_VIEWS_PER_DAY = 105       # перегляди розкладу персоналом
OWNER_REPORTS_PER_DAY = 3       # звіти власника

# Операції за добу: назва -> (кількість, {модуль: звернень за одну операцію})
OPERATIONS = {
    "Пошук вільного часу": (BOOKINGS_PER_DAY * SEARCHES_PER_BOOKING,
        {"Особистий кабінет": 1, "Онлайн-запис": 1, "Каталог послуг": 1,
         "Розклад": LOCATIONS}),
    "Створення запису": (BOOKINGS_PER_DAY,
        {"Особистий кабінет": 1, "Онлайн-запис": 1, "Розклад": 1,
         "Каталог послуг": 1, "Клієнтська база": 1, "Сповіщення": 1}),
    "Нагадування за 24 год": (BOOKINGS_PER_DAY,
        {"Онлайн-запис": 1, "Сповіщення": 1}),
    "Скасування і повторне заповнення": (CANCELLATIONS_PER_DAY,
        {"Особистий кабінет": 2, "Онлайн-запис": 1, "Розклад": 2,
         "Лист очікування": 1, "Сповіщення": 2, "Звіти": 2}),
    "Заявка в лист очікування": (WAITLIST_REQUESTS_PER_DAY,
        {"Особистий кабінет": 1, "Лист очікування": 1}),
    "Оплата": (BOOKINGS_PER_DAY,
        {"Оплата": 1, "Онлайн-запис": 1, "Звіти": 1}),
    "Перегляд розкладу персоналом": (STAFF_VIEWS_PER_DAY, {"Розклад": 1}),
    "Історія клієнта для майстра": (BOOKINGS_PER_DAY, {"Клієнтська база": 1}),
    "Звіт власника": (OWNER_REPORTS_PER_DAY, {"Звіти": 1, "Розклад": 1, "Оплата": 1}),
}


# ---------------------------------------------------------------------------
def load_json(filename):
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


# 1. Мережева модель процесу
def build_network(process):
    network = nx.DiGraph()
    for step_id, name, module, seconds in process["steps"]:
        network.add_node(step_id, name=name, module=module, seconds=seconds)
    for source, target in process["links"]:
        # вага ребра — тривалість кроку, до якого веде ребро
        network.add_edge(source, target, seconds=network.nodes[target]["seconds"])
    return network


def process_time(network, human_steps):
    """Критичний шлях — найдовший за часом шлях від початку до кінця процесу."""
    path = nx.dag_longest_path(network, weight="seconds")
    total = sum(network.nodes[step]["seconds"] for step in path)
    human = sum(network.nodes[step]["seconds"] for step in path if step in human_steps)
    return path, total, total - human


def time_to_offer(network, path):
    """Час від скасування до надсилання пропозиції кандидату (вимога NFR-02)."""
    seconds = 0
    for step in path:
        seconds += network.nodes[step]["seconds"]
        if network.nodes[step]["name"] == "Пропозиція кандидату":
            return seconds


# 2. Метод аналізу ієрархій Т. Сааті
def saaty(matrix):
    matrix = np.array(matrix)
    n = len(matrix)
    # ваги — середнє геометричне рядка, нормоване до суми 1
    row_means = np.prod(matrix, axis=1) ** (1 / n)
    weights = row_means / row_means.sum()
    # перевірка узгодженості суджень
    lambda_max = (matrix @ weights / weights).mean()
    consistency_index = (lambda_max - n) / (n - 1)
    consistency_ratio = consistency_index / RANDOM_INDEX[n]
    return weights, lambda_max, consistency_index, consistency_ratio


# 3. Математична модель навантаження
def module_load(modules):
    load = {module: 0 for module in modules}
    for count, calls in OPERATIONS.values():
        for module, calls_per_operation in calls.items():
            load[module] += count * calls_per_operation
    return load


def main_operation(module):
    """Операція, яка створює найбільше звернень до модуля."""
    best_name, best_calls = None, 0
    for name, (count, calls) in OPERATIONS.items():
        module_calls = count * calls.get(module, 0)
        if module_calls > best_calls:
            best_name, best_calls = name, module_calls
    return best_name, best_calls


def search_time(locations):
    return OVERHEAD_MS + QUERY_TIME_MS * locations


# 4. Проблемний модуль: важливий для BO-1 і сильно навантажений
def problem_score(weights, load):
    max_load = max(load.values())
    score = {}
    for module, weight in zip(SAATY_MODULES, weights):
        score[module] = weight * load[module] / max_load
    return score


# ---------------------------------------------------------------------------
# Графіки
def draw_network(network, critical_path, filename):
    # кроки, що виконуються одночасно, стоять в одному стовпці
    for layer, steps in enumerate(nx.topological_generations(network)):
        for step in steps:
            network.nodes[step]["layer"] = layer
    positions = nx.multipartite_layout(network, subset_key="layer")

    modules = sorted({network.nodes[s]["module"] for s in network.nodes})
    palette = dict(zip(modules, plt.cm.Pastel1.colors))
    colors = [palette[network.nodes[s]["module"]] for s in network.nodes]

    labels = {}
    for step, data in network.nodes(data=True):
        name = data["name"].replace(" ", "\n", 1)
        labels[step] = f"{step}\n{name}\n{data['seconds']:g} с"

    # ребра критичного шляху — червоні
    critical_edges = list(zip(critical_path, critical_path[1:]))
    edge_colors = ["red" if edge in critical_edges else "black" for edge in network.edges]

    plt.figure(figsize=(13, 5.5))
    nx.draw_networkx_edges(network, positions, node_size=6800, node_shape="s",
                           arrowsize=18, width=2, edge_color=edge_colors)
    nx.draw_networkx_nodes(network, positions, node_size=6800, node_shape="s",
                           node_color=colors, edgecolors="black")
    nx.draw_networkx_labels(network, positions, labels, font_size=9.5)
    for module in modules:
        plt.scatter([], [], marker="s", s=150, color=palette[module],
                    edgecolors="black", label=module)
    plt.plot([], [], color="red", linewidth=2, label="Критичний шлях")
    plt.legend(loc="lower left", fontsize=9, ncol=4)
    plt.axis("off")
    plt.margins(x=0.06, y=0.25)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


def draw_bar_chart(values, title, xlabel, filename):
    names = sorted(values, key=values.get)
    numbers = [values[name] for name in names]
    colors = ["#4a90d9"] * len(names)
    colors[-1] = "#e4572e"            # найбільше значення — червоним

    plt.figure(figsize=(10, 5))
    plt.barh(names, numbers, color=colors)
    for i, number in enumerate(numbers):
        plt.text(number, i, f" {number:g}", va="center")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
def main():
    system = load_json("system.json")
    process = load_json("process.json")

    network = build_network(process)
    path, total, system_seconds = process_time(network, process["human_steps"])
    offer_seconds = time_to_offer(network, path)

    weights, lambda_max, ci, cr = saaty(SAATY_MATRIX)
    load = module_load(system["modules"])
    score = problem_score(weights, load)

    most_important = SAATY_MODULES[int(np.argmax(weights))]
    most_loaded = max(load, key=load.get)
    problem = max(score, key=score.get)
    operation, operation_calls = main_operation(problem)

    draw_network(network, path, "process_network.png")
    draw_bar_chart({m: round(w, 3) for m, w in zip(SAATY_MODULES, weights)},
                   "Метод Сааті: важливість модулів для BO-1", "Вага", "saaty_weights.png")
    draw_bar_chart(load, "Математична модель: навантаження модулів",
                   "Звернень на добу", "module_load.png")

    lines = []
    lines.append(f"Інформаційна система: {system['name']}")
    lines.append(f"  Кількість модулів – {len(system['modules'])};")
    lines.append(f"  Кількість зв'язків – {len(system['links'])};")
    lines.append("  Тип структури – мережевий;")
    lines.append(f"  Модельований процес – «{process['name']}» "
                 f"({network.number_of_nodes()} кроків, {network.number_of_edges()} переходів);")
    lines.append("  Метод експертного аналізу – метод аналізу ієрархій Т. Сааті;")
    lines.append("  Метод математичного моделювання – аналітична модель часу процесу "
                 "та навантаження модулів;")
    lines.append("")
    lines.append(f"  Критичний шлях: {' -> '.join(path)}")
    lines.append(f"  Загальний час процесу – {total / 60:.1f} хв "
                 f"(з них робота системи – {system_seconds:.1f} с);")
    lines.append(f"  Час від скасування до пропозиції кандидату – {offer_seconds:.1f} с "
                 f"(NFR-02: до 60 с);")
    lines.append("")
    lines.append("  Ваги модулів за методом Сааті:")
    for module, weight in sorted(zip(SAATY_MODULES, weights), key=lambda x: -x[1]):
        lines.append(f"    {module}: {weight:.3f}")
    lines.append(f"  λmax = {lambda_max:.3f}; ІУ = {ci:.3f}; ВУ = {cr:.3f} "
                 f"({'судження узгоджені' if cr < 0.1 else 'судження НЕ узгоджені'});")
    lines.append("")
    lines.append("  Навантаження модулів (звернень на добу):")
    for module in sorted(load, key=load.get, reverse=True):
        lines.append(f"    {module}: {load[module]}")
    lines.append(f"  Час пошуку вільного часу на {LOCATIONS} локаціях – "
                 f"{search_time(LOCATIONS)} мс (NFR-01: до {SEARCH_LIMIT_MS} мс), "
                 f"на {LOCATIONS + 1} локаціях – {search_time(LOCATIONS + 1)} мс;")
    lines.append("")
    lines.append("  Оцінка проблемності (вага × частка навантаження):")
    for module in sorted(score, key=score.get, reverse=True):
        lines.append(f"    {module}: {score[module]:.3f}")
    lines.append(f"  Найважливіший модуль – «{most_important}»;")
    lines.append(f"  Найбільш навантажений модуль – «{most_loaded}»;")
    lines.append(f"  Проблемний модуль – «{problem}» ({operation_calls / load[problem]:.0%} "
                 f"звернень до нього створює операція «{operation}»);")
    lines.append("")
    lines.append("  Рекомендації:")
    lines.append(f"    1. Розвантажити модуль «{problem}»: винести операцію «{operation}» "
                 f"в окремий модуль з індексом вільних слотів усіх локацій.")
    lines.append(f"    2. Модуль «{most_important}» найважливіший для BO-1: покрити його "
                 f"тестами в першу чергу.")
    lines.append("    3. Сповіщення та облік у звітах виконувати асинхронно, щоб їхній "
                 "збій не зупиняв запис.")

    report = "\n".join(lines)
    print(report)
    with open("report.txt", "w", encoding="utf-8") as file:
        file.write(report)


if __name__ == "__main__":
    main()
