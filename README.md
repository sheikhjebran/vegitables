# Vegitables Project

### List all install package
```
pip freeze > requirements.txt
```

### To check python package 
```
pip-check
```
### To upgrade the insatlled package 
```
pip install pip-upgrader
pip-upgrade requirements.txt
```[README.md](README.md)

### To migrate the sql
```
python3 manage.py sqlmigrate shops 0002
```

### necessary plugin for django
```
pip install whitenoise
```

### Remove all .pyc file from project
```
find . -name "*.pyc" -exec rm -f {} \;
```
