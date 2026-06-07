# Fullstack demo (Flask + static frontend)

Instrucciones rápidas:

1. Activar el entorno virtual (PowerShell):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
. .\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias e iniciar la app:

```powershell
pip install -r requirements.txt
python app.py
```

Para MongoDB Atlas, define al menos `MONGODB_URI` o `MONGODB_ATLAS_URI`. Si quieres apuntar a una base concreta, agrega `MONGODB_DB`.

3. Abrir en el navegador: http://127.0.0.1:5000/
