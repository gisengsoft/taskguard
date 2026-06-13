from flask import Flask, render_template_string
from markupsafe import Markup

app = Flask(__name__)
with app.app_context():
    val = "A & B"
    print(render_template_string("{{ val }}", val=val))
