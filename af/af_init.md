# af_init

```bash

cd af
uv venv --clear
uv sync
uv run python -c "import sys; print(sys.executable)"
uv pip compile requirement.in --constraints constraints-3.9-update.txt --output-file requirement_win11.txt --refresh

pip3 install uv
mamba info --envs
mamba init

mamba remove -n base_py39 --all -y
mamba create -n base_py39 python==3.9.20 -y
mamba activate base_py39
pip3 install --upgrade pip
pip3 install uv
mamba deactivate

cd /opt/af
mamba activate base_py39
uv venv --clear
uv sync
mamba deactivate
uv run python -c "import sys; print(sys.executable)"
uv pip compile requirement.in --constraints constraints-3.9-update.txt --output-file requirement_rhel8.txt --refresh

```
