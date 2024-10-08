﻿# flybird-site

## Reference

- [github-repo](https://github.com/tishenme/flybird-site)
- [github-page](https://tishenme.github.io/flybird-site)

## Guideline

- Office cource

  - [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/getting-started/)

- Refernce cource

  - [Cloud Notes](https://notes.lzwang.ltd/Python/)
  - [create-blog](https://github.com/mkdocs-material/create-blog/blob/main/mkdocs.yml)
  - [Eureka!](http://www.cuishuaiwen.com:8000/zh/PROJECT/TECH-BLOG/mkdocs_and_material/)

## Use Conda & Poetry

```bash

# use conda control python version
conda deactivate
conda remove -n venv_conda_project_flybird-site --all -y
conda create python=3.12 -n venv_conda_project_flybird-site -y
conda activate venv_conda_project_flybird-site
python -m pip install --upgrade pip
pip install --upgrade pip
pip install --upgrade setuptools
pip list
conda deactivate
conda env list

# use poetry control python packages
python -m pip install --user pipx
python -m pip install --upgrade --user pipx
cd ~/AppData/Roaming/Python/Python312/Scripts
.\pipx.exe ensurepath --force
pipx install poetry -v
poetry --version

# config
poetry config --list
poetry config virtualenvs.in-project true

# init
cd D:\CodeWork\IDE_Microsoft_VSCode_Workspace
poetry new flybird-site

# venv ( default python version should be 3.12 )
poetry source add tsinghua https://pypi.tuna.tsinghua.edu.cn/simple

# use defalut python
poetry env remove python
poetry env use python
poetry env info

# use conda venv python
Remove-Item -Path .\.venv -Recurse
Remove-Item -Path .\poetry.lock -Recurse
conda env list
poetry env use "D:\CodeWork\DL_Python\venv_conda\venv_conda_project_flybird-site\python.exe"
poetry env use /opt/homebrew/Caskroom/miniconda/base/envs/venv_conda_project_flybird-site/bin/python

# poetry add [package-name]

# add package bgein
poetry add jinja2~=3.0
poetry add markdown~=3.2
poetry add mkdocs~=1.6
poetry add mkdocs-material==9.*
poetry add mkdocs-material-extensions~=1.3
poetry add pygments~=2.16
poetry add pymdown-extensions~=10.2
poetry add babel~=2.10
poetry add colorama~=0.4
poetry add paginate~=0.5
poetry add regex>=2022.4
poetry add requests~=2.26
poetry add mkdocs-minify-plugin
poetry add mkdocs-rss-plugin
poetry add mkdocs-static-i18n
poetry add mkdocs-table-reader-plugin
poetry add mkdocs-macros-plugin
# add package end

# poetry remove [package-name]

# update
poetry update
poetry show --tree

# shell
poetry shell
exit

# export
poetry export -f requirements.txt -o requirements.txt --without-hashes

# mkdocs command
poetry run mkdocs -h
poetry run mkdocs build
poetry run mkdocs serve

```
