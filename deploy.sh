cd /home/finance.danielmoessner.de/ || exit
git reset --hard HEAD
git pull
tmp/venv/bin/pip install .
tmp/venv/bin/python manage.py migrate
./permissions.sh
tmp/venv/bin/python manage.py collectstatic  --no-input
systemctl restart apache2
