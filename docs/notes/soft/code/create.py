import os

# 定义文件夹结构
folder_structure = {
    '系统工具': {
        '运行环境': [],
        '系统优化': [],
        '安全防护': [],
        '数据恢复': [],
        '破解工具': [],
        '窗口控制': [],
        '文件管理': []
    },
    '应用软件': {
        '壁纸墙纸': [],
        '日历时间': [],
        '效率时间': [],
        '办公软件': [],
        '书籍阅读': [],
        'PDF相关': [],
        '压缩刻录': [],
        '翻译工具': [],
        '财务金融': [],
        '手机管理': []
    },
    '图形设计': {
        '图片浏览': [],
        '图像处理': [],
        '动画制作': [],
        '三维动画': [],
        '交互工具': [],
        '设计辅助': []
    },
    '媒体工具': {
        '屏幕截图': [],
        '屏幕录像': [],
        '音乐播放': [],
        '音频编辑': [],
        '视频播放': [],
        '视频编辑': []
    },
    '网络工具': {
        '浏览器': [],
        '下载工具': [],
        '网络连接': [],
        '远程控制': [],
        '社交聊天': [],
        '邮件客户端': [],
        '网盘客户端': [],
    },
    '编程开发': {
        '虚拟机': [],
        '文本处理': [],
        '版本控制': [],
        '编程工具': [],
        '数据库工具': []
    }
}

def create_file_if_not_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding="utf-8") as file:
            file.write("软件,描述,官网地址,下载渠道,包管理")
        file.close()
    else:
        print(f"The file {file_path} already exists.")

# 创建文件夹和文件 ( docs\notes\soft\data )
base_path = os.path.join(os.getcwd(), "docs", "notes", "soft", "data")
for category, subcategories in folder_structure.items():
    print(category)
    print(subcategories)
    os.makedirs(os.path.join(base_path, category), exist_ok=True)
    for subcategory in subcategories:
        category_path = os.path.join(base_path, category, subcategory)
        category_path_win = category_path + "_win.csv"
        category_path_mac = category_path + "_mac.csv"
        create_file_if_not_exists(category_path_win)
        create_file_if_not_exists(category_path_mac)
