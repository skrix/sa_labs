"""
Системний аналіз. Практична робота №3.
Автоматизоване формування технічної специфікації інформаційної системи.

Програма читає опис системи з файлу spec_input.json, перевіряє,
чи вистачає вимог і бізнес-правил, формує технічну специфікацію
у форматі Markdown (technical_specification.md) і короткий звіт.
"""
import json

# Мінімальна кількість елементів за завданням
MINIMUM = {
    "functional": 8,      # функціональні вимоги
    "nonfunctional": 5,   # нефункціональні вимоги
    "business_rules": 5,  # бізнес-правила
}


def load_spec(filename):
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def check_spec(spec):
    """Повертає список зауважень; порожній список — усе гаразд."""
    problems = []
    for key, minimum in MINIMUM.items():
        if len(spec[key]) < minimum:
            problems.append(f"{key}: потрібно не менше {minimum}, є {len(spec[key])}")
    return problems


def table(header, rows):
    """Таблиця Markdown: заголовок, роздільник і рядки."""
    lines = ["| " + " | ".join(header) + " |",
             "|" + "---|" * len(header)]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def build_markdown(spec):
    md = []
    md.append(f"# Технічна специфікація: {spec['name']}")

    md.append("\n## 1. Призначення системи")
    md.append(spec["purpose"])
    md.append("\nЗовнішні системи: " + ", ".join(spec["external_systems"]) + ".")

    md.append("\n## 2. Програмні модулі\n")
    rows = []
    for m in spec["modules"]:
        rows.append([m["name"], m["purpose"], m["functions"], m["modules"], m["external"]])
    md += table(["Модуль", "Призначення", "Основні функції",
                 "Взаємодія з модулями", "Зовнішня взаємодія"], rows)

    md.append("\n## 3. Функціональні вимоги\n")
    md += table(["ID", "Вимога"], spec["functional"])

    md.append("\n## 4. Нефункціональні вимоги\n")
    md += table(["ID", "Категорія", "Вимога"], spec["nonfunctional"])

    md.append("\n## 5. Бізнес-правила\n")
    md += table(["ID", "Правило"], spec["business_rules"])

    use_case = spec["use_case"]
    md.append("\n## 6. Сценарій використання")
    md.append(f"### {use_case['name']}")
    md.append(f"**Учасники:** {use_case['actors']}\n")
    md.append(f"**Початкова умова:** {use_case['precondition']}\n")
    steps = []
    for number, (action, reaction) in enumerate(use_case["main_flow"], start=1):
        steps.append([number, action, reaction])
    md += table(["№", "Дія користувача", "Реакція системи"], steps)
    md.append(f"\n**Результат:** {use_case['result']}\n")
    md.append("**Альтернативні сценарії:**")
    for item in use_case["alternatives"]:
        md.append(f"- {item}")
    md.append("\n**Виняткові ситуації:**")
    for item in use_case["exceptions"]:
        md.append(f"- {item}")

    md.append("\n## 7. Взаємодія модулів\n")
    md += table(["Відправник", "Отримувач", "Дані", "Призначення"], spec["interactions"])

    api = spec["api"]
    md.append(f"\n### Приклад API: {api['title']}")
    md.append("Запит:\n```\n" + api["request"] + "\n```")
    md.append("Відповідь:\n```\n" + api["response"] + "\n```")
    md.append(f"Помилки: {api['errors']}")

    md.append("\n## 8. Обмеження")
    for item in spec["constraints"]:
        md.append(f"- {item}")

    md.append("\n## 9. Припущення")
    for item in spec["assumptions"]:
        md.append(f"- {item}")

    return "\n".join(md) + "\n"


def make_report(spec, created):
    lines = [
        f"Інформаційна система: {spec['name']}",
        f"  Кількість програмних модулів — {len(spec['modules'])};",
        f"  Кількість функціональних вимог — {len(spec['functional'])};",
        f"  Кількість нефункціональних вимог — {len(spec['nonfunctional'])};",
        f"  Кількість бізнес-правил — {len(spec['business_rules'])};",
        f"  Кількість основних взаємодій між модулями — {len(spec['interactions'])};",
        f"  Кількість зовнішніх систем — {len(spec['external_systems'])};",
        f"  Кількість обмежень / припущень — {len(spec['constraints'])} / "
        f"{len(spec['assumptions'])};",
        f"  Основний сценарій — «{spec['main_scenario']}»;",
        f"  Сформовано технічну специфікацію — {'так' if created else 'ні'}.",
    ]
    return "\n".join(lines)


def main():
    spec = load_spec("spec_input.json")

    problems = check_spec(spec)
    for problem in problems:
        print("Зауваження:", problem)

    created = not problems
    if created:
        with open("technical_specification.md", "w", encoding="utf-8") as file:
            file.write(build_markdown(spec))

    report = make_report(spec, created)
    print(report)
    with open("report.txt", "w", encoding="utf-8") as file:
        file.write(report)


main()
