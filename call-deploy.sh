pdm run pytest . || exit
ssh root@46.101.136.214 /home/finance.danielmoessner.de/deploy.sh
