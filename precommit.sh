#!/bin/bash

printf "djlint:\n"
uv run djlint apps/*/jinja2/**/* templates/**/* --max-line-length=120 --profile=jinja --reformat --include="*.j2"
printf "\nisort:\n" && uv run isort . --profile black
printf "\n\n"
printf "black:\n" && uv run black .
printf "\n\n"
printf "ruff:\n"  && uv run ruff check . --fix
printf "\n\n"
# printf "mypy:\n"  && uv run mypy .
# printf "\n\n"
