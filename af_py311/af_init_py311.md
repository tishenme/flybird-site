# af_init

- [](https://raw.githubusercontent.com/apache/airflow/constraints-2.7.3/constraints-3.11.txt)

```bash

cd af
uv venv --clear
uv sync
uv run python -c "import sys; print(sys.executable)"
uv pip compile requirements.in --constraints constraints-3.9-update.txt --output-file requirements_win11.txt --refresh

pip3 install uv
mamba info --envs
mamba init

mamba remove -n base_py311 --all -y
mamba create -n base_py311 python==3.11.14 -y
mamba activate base_py311
pip3 install --upgrade pip
pip3 install uv
mamba deactivate

cd /opt/af
mamba activate base_py311
uv venv --clear
uv sync
mamba deactivate
uv run python -c "import sys; print(sys.executable)"
uv pip compile requirements.in --constraints constraints_update.txt --output-file requirements_rhel8.txt --refresh

uv run python -m ensurepip --upgrade
deactivate && source .venv/bin/activate
# which pip3 && pip3 install --upgrade pip
pip3 download -r requirements_rhel8.txt -d ./packages
pip3 install --no-index --find-links=./packages -r requirements_rhel8.txt
deactivate

pip3 download wheel setuptools build -d ./packages
dnf install -y gcc openldap-devel

zip -r packages_airflow_20703_py311_20260303.zip ./packages

split -b 99M packages_airflow_20703_py311_20260303.zip packages_airflow_part_
cat packages_airflow_part_* > packages_airflow_20703_py311_20260303.zip
unzip packages_airflow_20703_py311_20260303.zip

```
