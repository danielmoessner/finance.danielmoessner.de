git reset --hard HEAD
git pull
tmp/venv/bin/pip install -r requirements.txt
tmp/venv/bin/python manage.py migrate
./permissions.sh
npm install
npm run build
systemctl restart apache2
