from flask import Flask, render_template_string
import html

app = Flask(__name__)
with app.app_context():
    val = html.escape("A & B", quote=True)
    print(render_template_string("{{ val }}", val=val))
