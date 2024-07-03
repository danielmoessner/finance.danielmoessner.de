#!/bin/bash

printf "djlint:\n"
pdm run djlint . ./pyproject.toml --max-line-length=120 --profile=jinja --reformat
printf "\nisort:\n" && pdm run isort . --profile black
printf "\n\n"
printf "black:\n" && pdm run black .
printf "\n\n"
printf "ruff:\n"  && pdm run ruff check . --fix
printf "\n\n"
# printf "mypy:\n"  && pdm run mypy .
# printf "\n\n"
