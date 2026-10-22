"""
Системний аналіз. Практична робота №1. Аналіз предметної області.

Програма читає опис інформаційної системи з файлу system.json,
рахує її показники, будує граф взаємозв'язків і формує звіт.
"""
import json
import math

import matplotlib.pyplot as plt
import networkx as nx

# Вигляд графа
MODULE_COLOR = "#4a90d9"      # звичайний модуль
CENTER_COLOR = "#e4572e"      # найбільш зв'язаний модуль
EXTERNAL_COLOR = "#ffd580"    # зовнішній компонент
INNER_LINK_COLOR = "#2c5d8f"  # зв'язок між модулями
OUTER_LINK_COLOR = "#c98a1b"  # взаємодія із зовнішнім середовищем
MODULE_SIZE = 6500
EXTERNAL_SIZE = 7000


# 1. Зчитування опису системи
def load_system(filename):
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


# 2. Побудова графа: вузли — компоненти, ребра — зв'язки
def build_graph(system):
    graph = nx.DiGraph()
    graph.add_nodes_from(system["modules"])
    graph.add_nodes_from(system["external"])
    for source, target, _description in system["links"]:
        graph.add_edge(source, target)   # опис зв'язку в графі не потрібен
    return graph


# 3. Аналіз системи
def analyze(graph, system):
    modules = system["modules"]
    external = system["external"]

    # кількість зв'язків кожного модуля (вхідні + вихідні)
    links_count = {}
    for module in modules:
        links_count[module] = graph.degree(module)

    max_links = max(links_count.values())
    most_connected = [m for m in modules if links_count[m] == max_links]
    isolated = [m for m in modules if links_count[m] == 0]

    # з якими зовнішніми компонентами взаємодіє кожен модуль
    boundary = {}
    inner_only = []
    for module in modules:
        partners = [n for n in nx.all_neighbors(graph, module) if n in external]
        if partners:
            boundary[module] = sorted(set(partners))
        else:
            inner_only.append(module)

    return {
        "links_count": links_count,
        "most_connected": most_connected,
        "max_links": max_links,
        "isolated": isolated,
        "boundary": boundary,
        "inner_only": inner_only,
    }


# 4. Побудова графа: найбільш зв'язаний модуль — у центрі,
#    інші модулі — навколо нього (система), зовнішні компоненти — зовнішнім колом
def draw_graph(graph, system, result, filename):
    modules = system["modules"]
    external = system["external"]
    center = result["most_connected"][0]
    other_modules = [m for m in modules if m != center]
    positions = nx.shell_layout(graph, nlist=[[center], other_modules, external], rotate=0)

    plt.figure(figsize=(12, 12))

    # межа системи — коло трохи більше за коло модулів
    x, y = positions[other_modules[0]]
    system_radius = math.hypot(x, y) + 0.12
    border = plt.Circle((0, 0), system_radius, facecolor="#eef4fb",
                        edgecolor=INNER_LINK_COLOR, linestyle="--", linewidth=2)
    plt.gca().add_patch(border)
    plt.text(0, system_radius + 0.03, "СИСТЕМА", ha="center", fontsize=14,
             color=INNER_LINK_COLOR, weight="bold")

    x, y = positions[external[0]]
    outer_radius = math.hypot(x, y)
    plt.text(-outer_radius, -outer_radius, "ЗОВНІШНЄ СЕРЕДОВИЩЕ", fontsize=14,
             color=OUTER_LINK_COLOR, weight="bold")

    # зв'язки: між модулями — суцільні, із середовищем — пунктирні
    inner_links = [(a, b) for a, b in graph.edges if a in modules and b in modules]
    outer_links = [(a, b) for a, b in graph.edges if (a, b) not in inner_links]
    nx.draw_networkx_edges(graph, positions, edgelist=inner_links, edge_color=INNER_LINK_COLOR,
                           width=1.5, arrowsize=15, node_size=MODULE_SIZE)
    nx.draw_networkx_edges(graph, positions, edgelist=outer_links, edge_color=OUTER_LINK_COLOR,
                           width=1.5, arrowsize=15, node_size=EXTERNAL_SIZE, style="dashed")

    # вузли: модулі — кола, найбільш зв'язаний — червоний; зовнішні — квадрати
    colors = [CENTER_COLOR if m == center else MODULE_COLOR for m in modules]
    nx.draw_networkx_nodes(graph, positions, nodelist=modules, node_color=colors,
                           node_size=MODULE_SIZE, edgecolors="black")
    nx.draw_networkx_nodes(graph, positions, nodelist=external, node_color=EXTERNAL_COLOR,
                           node_size=EXTERNAL_SIZE, node_shape="s", edgecolors="black")

    labels = {node: node.replace(" ", "\n") for node in graph.nodes}
    nx.draw_networkx_labels(graph, positions, labels, font_size=10)

    plt.axis("equal")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


# 5. Формування звіту
def make_report(graph, system, result):
    lines = []
    lines.append(f"Інформаційна система: {system['name']}")
    lines.append(f"  Кількість модулів: {len(system['modules'])}")
    lines.append(f"  Кількість зовнішніх компонентів: {len(system['external'])}")
    lines.append(f"  Кількість зв'язків: {graph.number_of_edges()}")
    lines.append(f"  Найбільш зв'язаний модуль: «{', '.join(result['most_connected'])}» "
                 f"({result['max_links']} зв'язків)")
    if result["isolated"]:
        lines.append(f"  Ізольовані модулі: {', '.join(result['isolated'])}")
    else:
        lines.append("  Ізольовані модулі: відсутні")

    lines.append("  Зовнішні компоненти:")
    for component in system["external"]:
        lines.append(f"    - {component}")

    # модулі від найбільш до найменш зв'язаного
    lines.append("  Кількість зв'язків кожного модуля:")
    counts = result["links_count"]
    for module in sorted(counts, key=counts.get, reverse=True):
        lines.append(f"    {module}: {counts[module]}")

    lines.append("  Модулі, що взаємодіють із зовнішнім середовищем:")
    for module, partners in result["boundary"].items():
        lines.append(f"    {module} -> {', '.join(partners)}")
    lines.append(f"  Модулі, що працюють лише всередині системи: "
                 f"{', '.join(result['inner_only'])}")

    return "\n".join(lines)


def main():
    system = load_system("system.json")
    graph = build_graph(system)
    result = analyze(graph, system)
    draw_graph(graph, system, result, "system_graph.png")

    report = make_report(graph, system, result)
    print(report)
    with open("report.txt", "w", encoding="utf-8") as file:
        file.write(report)


if __name__ == "__main__":
    main()
