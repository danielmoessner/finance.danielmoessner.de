#!/bin/bash

printf "\nisort:\n" && pdm run isort . --profile black
printf "\n\n"
printf "black:\n" && pdm run black .
printf "\n\n"
printf "ruff:\n"  && pdm run ruff check . --fix
printf "\n\n"
# printf "mypy:\n"  && pdm run mypy .
# printf "\n\n"
