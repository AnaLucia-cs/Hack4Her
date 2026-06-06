import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Proyecto import app

c = app.test_client()
r = c.get('/')
html = r.data.decode('utf-8')
i = html.find('styles.css')
if i == -1:
    print('NOT_FOUND')
else:
    start = html.rfind('href="', 0, i)
    end = html.find('"', i)
    link = html[start+6:end]
    print(link)
    print('HAS_V' if '?v=' in link else 'NO_V')
