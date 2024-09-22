# Mac

!!! tip
    Mac 手成本高 但是带来的体验是非常棒的 除非找不到你想要的软件

## Homebrew

- 安装 xcode 命令行工具

    ```zsh
    xcode-select --install
    ```

- 安装脚本 ( [国内源](https://gitee.com/cunkai/HomebrewCN) )

    ```zsh
    /bin/zsh -c "$(curl -fsSL https://gitee.com/cunkai/HomebrewCN/raw/master/Homebrew.sh)"
    ```

- 卸载脚本 ( [国内源](https://gitee.com/cunkai/HomebrewCN) )

    ```zsh
    /bin/zsh -c "$(curl -fsSL https://gitee.com/cunkai/HomebrewCN/raw/master/HomebrewUninstall.sh)"
    ```

- 安装软件

    - 请在 [Homebrew Formulae](https://formulae.brew.sh/) 搜索软件

        ![img](../image/homebrew.png)
        ![img](../image/wpsoffice-cn.png)

    - 执行安装命令

    ```zsh
    brew install --cask wpsoffice-cn
    ```

- 卸载软件

    - 执行卸载命令

    ```zsh
    brew uninstall --cask wpsoffice-cn
    ```

## 优化指南

- [加快网络共享内容的浏览速度](https://support.apple.com/zh-cn/102064)

    - `要加快 SMB 文件的浏览速度，你可以阻止 macOS 读取 SMB 共享上的 .DS_Store 文件。这样，“访达”将只使用基本信息来立即以字母数字顺序显示各个文件夹的内容。请使用以下终端命令：`

    ```zsh
    defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool TRUE
    ```

## 装机必备

- ### 系统工具

    | 软件 | 描述  | 官网地址 | 下载渠道 | brew 安装命令 |
    | :--- | :---- | :------- | :------- | :------------ |
    | xxxx | xxxxx | xxxxx    |          |               |
