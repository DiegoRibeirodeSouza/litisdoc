import re

with open("litisdoc/backends/dossier.py", "r") as f:
    content = f.read()

if "import textwrap" not in content:
    content = content.replace("import tempfile", "import tempfile\nimport textwrap")

old_code = """    # Título principal centralizado no meio da página
    c.setFont(f_title, 28)
    y_center = A4_HEIGHT / 2
    c.drawCentredString(A4_WIDTH / 2, y_center + 40, title.upper())"""

new_code = """    # Título principal centralizado no meio da página
    c.setFont(f_title, 28)
    y_center = A4_HEIGHT / 2
    lines = textwrap.wrap(title.upper(), width=35)
    y_pos = y_center + 40 + (len(lines) - 1) * 35
    for line in lines:
        c.drawCentredString(A4_WIDTH / 2, y_pos, line)
        y_pos -= 35"""

content = content.replace(old_code, new_code)

with open("litisdoc/backends/dossier.py", "w") as f:
    f.write(content)
