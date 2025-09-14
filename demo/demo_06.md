### USER
需要在 jupyterlab 首页固定显示 ailab 字眼 怎么实现?

### ASSISTANT
要在 JupyterLab 首页固定显示 “ailab” 字样，有几种实现方式，取决于你希望显示的位置、样式、以及是否需要持久化（重启后依然存在）。以下是几种实用方案：

---

## ✅ 方案一：修改 JupyterLab 启动页 HTML（推荐用于简单静态显示）

JupyterLab 的启动页（Launcher）是动态生成的，但你可以通过自定义 HTML 模板或注入 JS/CSS 来实现。

### 步骤：

1. **找到 Jupyter 配置目录**

   ```bash
   jupyter --config-dir
   # 通常位于 ~/.jupyter
   ```

2. **创建自定义 CSS 文件**

   在配置目录下创建 `custom` 文件夹和 CSS 文件：

   ```bash
   mkdir -p ~/.jupyter/custom
   nano ~/.jupyter/custom/custom.css
   ```

   写入以下 CSS（在页面左上角固定显示）：

   ```css
   body::before {
       content: "ailab";
       position: fixed;
       top: 10px;
       left: 10px;
       background-color: #444;
       color: white;
       padding: 5px 10px;
       border-radius: 4px;
       font-weight: bold;
       font-size: 14px;
       z-index: 9999;
   }
   ```

3. **重启 JupyterLab**

   关闭并重新启动 JupyterLab，即可在所有页面左上角看到 “ailab”。

> ✅ 优点：简单、无需插件、重启后依然有效
> ❗ 注意：这个会显示在所有页面，不只是首页

---

## ✅ 方案二：使用 JupyterLab 扩展（Extension）自定义启动页

如果你想**只在 Launcher 页面**（首页）显示，需要开发或使用扩展。

### 方法 1：使用现有扩展（如 `jupyterlab-topbar`）

安装一个支持自定义顶部栏的扩展：

```bash
pip install jupyterlab-topbar
jupyter lab build  # 可能需要
```

然后在设置中添加自定义文本（部分扩展支持）。

> ⚠️ 但目前没有直接支持“仅首页显示文本”的现成扩展。

---

### 方法 2：自己写一个简单的 JupyterLab 扩展（进阶）

1. 使用 `cookiecutter` 创建扩展模板：

   ```bash
   pip install cookiecutter
   cookiecutter https://github.com/jupyterlab/extension-cookiecutter-ts
   # 填写信息，比如 extension name: "ailab-banner"
   ```

2. 在生成的项目中，修改 `src/index.ts`，监听 launcher 被激活的事件：

   ```ts
   import {
     JupyterFrontEnd,
     JupyterFrontEndPlugin
   } from '@jupyterlab/application';

   import { ILabShell } from '@jupyterlab/application';

   const plugin: JupyterFrontEndPlugin<void> = {
     id: 'ailab-banner-plugin',
     autoStart: true,
     requires: [ILabShell],
     activate: (app: JupyterFrontEnd, shell: ILabShell) => {
       console.log('ailab banner plugin activated!');

       shell.currentChanged.connect((_, change) => {
         const current = change.newValue;
         if (current && current.title.label === 'Launcher') {
           // 在 launcher 页面添加 banner
           let banner = document.getElementById('ailab-banner');
           if (!banner) {
             banner = document.createElement('div');
             banner.id = 'ailab-banner';
             banner.style.position = 'fixed';
             banner.style.top = '10px';
             banner.style.left = '50%';
             banner.style.transform = 'translateX(-50%)';
             banner.style.background = '#007acc';
             banner.style.color = 'white';
             banner.style.padding = '8px 16px';
             banner.style.borderRadius = '4px';
             banner.style.zIndex = '10000';
             banner.innerText = 'ailab';
             document.body.appendChild(banner);
           }
           banner.style.display = 'block';
         } else {
           let banner = document.getElementById('ailab-banner');
           if (banner) {
             banner.style.display = 'none';
           }
         }
       });
     }
   };

   export default plugin;
   ```

3. 构建并安装：

   ```bash
   jlpm install
   jlpm run build
   jupyter labextension install .
   ```

4. 重启 JupyterLab，打开 Launcher 页面即可看到 “ailab” 居中显示。

> ✅ 优点：精准控制显示位置和页面
> ❗ 缺点：需要 Node.js 环境和构建步骤

---

## ✅ 方案三：修改 JupyterLab 启动命令 + 浏览器书签（最轻量）

如果你只是想“每次打开看到”，可以在启动命令或书签里加提示：

- 启动时终端打印：

  ```bash
  echo "=== WELCOME TO AILAB ==="
  jupyter lab
  ```

- 或者浏览器书签名称改为 “AILAB - JupyterLab”

> 这不是页面内显示，但对用户心理暗示有效 😊

---

## ✅ 方案四：修改 JupyterLab 的欢迎信息（通过 settings）

JupyterLab 本身没有直接设置首页标题的选项，但你可以：

- 修改浏览器标签页标题（通过 JS 注入）：

  在 `~/.jupyter/custom/custom.js`：

  ```js
  setTimeout(() => {
    document.title = "AILAB - JupyterLab";
  }, 1000);
  ```

  再配合前面的 CSS，实现标题+角标双重提示。

---

## 🏁 推荐做法：

- 如果你只是想**简单、全局显示** → 用 **方案一（CSS）**
- 如果你希望**只在首页显示、更专业** → 用 **方案二（自定义扩展）**
- 如果你是管理员部署给多人 → 推荐打包成扩展或预装 CSS

---

## 🧪 验证是否生效

无论哪种方法，重启 JupyterLab 后刷新页面，检查是否出现 “ailab” 字样。

---

如有更多需求（比如点击跳转、动态内容、多语言等），可基于扩展方案进一步开发。

需要我帮你生成完整扩展包或部署脚本吗？欢迎继续提问！
