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

mamba remove -n base_py309 --all -y
mamba create -n base_py309 python==3.9.20 -y
mamba activate base_py309
pip3 install --upgrade pip
pip3 install uv
mamba deactivate

cd /opt/af
mamba activate base_py309
uv venv --clear
uv sync
mamba deactivate
uv run python -c "import sys; print(sys.executable)"
uv pip compile requirement.in --constraints constraints_update.txt --output-file requirement_rhel8.txt --refresh

uv run python -m ensurepip --upgrade
deactivate && source .venv/bin/activate
# which pip3 && pip3 install --upgrade pip
pip3 download -r requirement_rhel8.txt -d ./packages
pip3 install --no-index --find-links=./packages -r requirement_rhel8.txt
deactivate

pip3 download wheel setuptools build -d ./packages
dnf install -y gcc openldap-devel

zip -r packages_airflow_20703_py39_20260116.zip ./packages

split -b 99M packages_airflow_20703_py39_20260116.zip packages_airflow_part_
cat packages_airflow_part_* > packages_airflow_20703_py39_20260116.zip
unzip packages_airflow_20703_py39_20260116.zip

```
