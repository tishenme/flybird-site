# flybird-site

## Reference

- [github-repo](https://github.com/tishenme/flybird-site)
- [github-page](https://tishenme.github.io/flybird-site)

## Guideline

- 官方教程

  - [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/getting-started/)

- 参考博客

  - [未央学习](https://weyoung-learn.github.io/skills/mkdocs/)
  - [Eureka!](http://www.cuishuaiwen.com:8000/zh/PROJECT/TECH-BLOG/mkdocs_and_material/)
  - [Cloud Notes](https://notes.lzwang.ltd/Python/)
  - [create-blog](https://github.com/mkdocs-material/create-blog/blob/main/mkdocs.yml)

## Use poetry

```bash

# use poetry control python project
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

# venv
poetry source add tsinghua https://pypi.tuna.tsinghua.edu.cn/simple
poetry env remove python
poetry env use python
poetry env info

# shell
poetry shell
exit

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
# add package end

# poetry remove requests

# update
poetry update
poetry show --tree

# export
poetry export -f requirements.txt -o requirements.txt --without-hashes

```

## Use Conda

```bash

# use poetry control python project
conda deactivate
conda remove -n venv_conda_312_mkdocs --all -y
conda create python=3.12 -n venv_conda_39_mkdocs -y
conda activate venv_conda_39_mkdocs
python.exe -m pip install --upgrade pip
pip install --upgrade pip
pip install --upgrade setuptools
pip list

# install
conda activate venv_conda_312_mkdocs
pip install -r requirements.txt

# upgrade
conda activate venv_conda_312_mkdocs
pip install --upgrade --force-reinstall mkdocs-material
pip show mkdocs-material

# help
conda activate venv_conda_312_mkdocs
mkdocs --help

# init project
cd D:\CodeWork\IDE_Microsoft_VSCode_Workspace
conda activate venv_conda_312_mkdocs
mkdocs new flybird-site

# Build the website
conda activate venv_conda_312_mkdocs
mkdocs build

# Run the website
conda activate venv_conda_312_mkdocs
mkdocs serve
```
