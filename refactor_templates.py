import re
import os

# 1. Create base_empty.html
base_empty = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}ScholarSync{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  {% block head %}{% endblock %}
  <style>
    body { font-family: 'Inter', sans-serif; }
    {% block styles %}{% endblock %}
  </style>
</head>
<body class="{% block body_class %}min-h-screen bg-slate-50 font-sans{% endblock %}">
  {% block content %}{% endblock %}
  {% block scripts %}{% endblock %}
</body>
</html>
"""
with open('templates/base_empty.html', 'w') as f:
    f.write(base_empty)

# 2. Refactor profile.html
with open('templates/profile.html', 'r') as f:
    p_content = f.read()

style_match = re.search(r'<style>([\s\S]*?)<\/style>', p_content)
if style_match:
    p_styles = style_match.group(1).replace("body { font-family: 'Inter', sans-serif; }", "").replace(".nav-active { background: #eef2ff; color: #4338ca; font-weight: 600; }", "").replace(".nav-active svg { color: #4f46e5; }", "").strip()
else:
    p_styles = ""

main_match = re.search(r'<main[^>]*>([\s\S]*?)<\/main>', p_content)
p_main = main_match.group(1).strip() if main_match else ""

script_match = re.search(r'<\/main>\s*([\s\S]*?)<\/body>', p_content)
if script_match:
    p_scripts = script_match.group(1).strip()
    # Remove sidebar toggle scripts
    p_scripts = re.sub(r'function openSidebar\(\) \{[\s\S]*?\}', '', p_scripts)
    p_scripts = re.sub(r'function closeSidebar\(\) \{[\s\S]*?\}', '', p_scripts)
else:
    p_scripts = ""

p_new = f"""{{% extends "base.html" %}}
{{% block title %}}Profile – ScholarSync{{% endblock %}}

{{% block styles %}}
{p_styles}
{{% endblock %}}

{{% block content %}}
<div class="flex-1 flex flex-col min-w-0 overflow-hidden">
{p_main}
</div>
{{% endblock %}}

{{% block scripts %}}
{p_scripts}
{{% endblock %}}
"""
with open('templates/profile.html', 'w') as f:
    f.write(p_new)

# 3. Refactor onboarding.html
with open('templates/onboarding.html', 'r') as f:
    o_content = f.read()

o_style_match = re.search(r'<style>([\s\S]*?)<\/style>', o_content)
if o_style_match:
    o_styles = o_style_match.group(1).replace("body {\n        font-family: \"Inter\", sans-serif;\n      }", "").strip()
else:
    o_styles = ""

o_body_match = re.search(r'<body[^>]*>\s*<!-- Logo -->([\s\S]*?)<script>', o_content)
o_main = o_body_match.group(1).strip() if o_body_match else ""

o_script_match = re.search(r'(<script>[\s\S]*?)<\/body>', o_content)
o_scripts = o_script_match.group(1).strip() if o_script_match else ""

o_new = f"""{{% extends "base_empty.html" %}}
{{% block title %}}Welcome to ScholarSync - Onboarding{{% endblock %}}

{{% block body_class %}}min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex flex-col items-center justify-center p-4{{% endblock %}}

{{% block styles %}}
{o_styles}
{{% endblock %}}

{{% block content %}}
<!-- Logo -->
{o_main}
{{% endblock %}}

{{% block scripts %}}
{o_scripts}
{{% endblock %}}
"""
with open('templates/onboarding.html', 'w') as f:
    f.write(o_new)

print("Refactored templates!")
