from pathlib import Path

path = Path("/app/client/dist/index.html")
html = path.read_text()
link = '<link rel="stylesheet" href="/static/dashboard.css?v=10">'

if html.count("</head>") != 1:
    raise RuntimeError("Не найдена ожидаемая структура HTML Redash")

if link not in html:
    path.write_text(html.replace("</head>", link + "</head>"))