# af_init

```bash

cd af
uv venv --clear
uv sync
uv run python -c "import sys; print(sys.executable)"
uv pip compile requirement.in --constraints constraints-3.9-update.txt --output-file requirement_win11.txt --refresh

```
