from Proyecto import app
c=app.test_client()
r=c.get('/')
html=r.data.decode('utf-8')
idx_script=html.find('src="/static/js/script.js"')
idx_body=html.find('</body>')
print('SCRIPT_FOUND', idx_script!=-1)
print('SCRIPT_BEFORE_BODY', idx_script!=-1 and idx_script < idx_body)
print(html[idx_script-40:idx_script+60])
