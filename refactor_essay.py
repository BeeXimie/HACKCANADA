import re

with open('templates/essay_vault.html', 'r') as f:
    e_content = f.read()

style_match = re.search(r'<style>([\s\S]*?)<\/style>', e_content)
if style_match:
    e_styles = style_match.group(1).replace("body { font-family: 'Inter', sans-serif; background-color: #f8fafc; }", "").replace(".nav-active { background: #eef2ff; color: #4338ca; font-weight: 600; }", "").replace(".nav-active svg { color: #4f46e5; }", "").strip()
else:
    e_styles = ""

main_match = re.search(r'<main[^>]*>([\s\S]*?)<\/main>', e_content)
e_main = main_match.group(1).strip() if main_match else ""

script_match = re.search(r'<\/main>\s*([\s\S]*?)<\/body>', e_content)
e_scripts = script_match.group(1).strip() if script_match else ""
e_scripts = re.sub(r'function openSidebar\(\) \{[\s\S]*?\}', '', e_scripts)
e_scripts = re.sub(r'function closeSidebar\(\) \{[\s\S]*?\}', '', e_scripts)

e_new = f"""{{% extends "base.html" %}}
{{% block title %}}Essay Vault | ScholarSync{{% endblock %}}

{{% block styles %}}
{e_styles}
{{% endblock %}}

{{% block content %}}
<div class="flex-1 flex flex-col min-w-0 overflow-hidden">
{e_main}
</div>
{{% endblock %}}

{{% block scripts %}}
{e_scripts}
{{% endblock %}}
"""
with open('templates/essay_vault.html', 'w') as f:
    f.write(e_new)
print("done")
