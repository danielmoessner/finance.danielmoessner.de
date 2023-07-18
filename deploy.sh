git reset --hard HEAD
git pull
tmp/venv/bin/pip install -r requirements.txt
tmp/venv/bin/python manage.py migrate
./permissions.sh
tmp/venv/bin/python manage.py collectstatic
systemctl restart apache2
