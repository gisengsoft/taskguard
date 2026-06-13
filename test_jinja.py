from jinja2 import Template
import html
template = Template("{{ task_title }}")
val1 = "A & B"
val2 = html.escape(val1, quote=True)
print("no escape:", template.render(task_title=val1))
print("with escape:", template.render(task_title=val2))
