import pandas as pd
from io import StringIO

# 假设这是你的 Markdown 表格原始代码
markdown_table = """

| 软件                | 描述                             | 官网地址                                                 | 下载渠道                                      |
| :------------------ | :------------------------------- | :------------------------------------------------------- | :-------------------------------------------- |
| 360 安全卫士-极速版 | 安全防护 推荐极速版 无广告无弹窗 | [官网地址](https://weishi.360.cn/jisu/?source=homepage/) |                                               |
| 火绒                | 专业尽职 极致低调                | [官网地址](https://www.huorong.cn/person5.html)          |                                               |
| CCleaner            | 系统优化和隐私保护工具           | [官网地址](https://www.ccleaner.com)                     | [下载渠道](https://www.423down.com/716.html)  |
| Geek                | 免费的软件卸载利器               | [官网地址](https://geekuninstaller.com)                  | [下载渠道](https://www.423down.com/2668.html) |
| Wise Care 365       | 世界上最快的系统优化软件         | [官网地址](https://www.wisecleaner.com.cn)               | [下载渠道](https://www.423down.com/3471.html) |

| 软件               | 描述                         | 官网地址                                                                                  | 下载渠道                                                                        |
| :----------------- | :--------------------------- | :---------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| 傲梅分区助手       | 好用的硬盘管理工具           | [官网地址](https://www.disktool.cn)                                                       | [下载渠道](https://www.423down.com/5969.html)                                   |
| 图吧工具箱         | 最纯净的硬件工具箱           | [官网地址](http://www.tbtool.cn/index.html)                                               |                                                                                 |
| 鲁大师             | 下载都是来跑个分             | [官网地址](https://www.ludashi.com/page/pc.php)                                           | [下载渠道](https://www.423down.com/3732.html)                                   |
| 360 驱动大师       | 驱动精灵 驱动人生广告太多了  | [官网地址](https://weishi.360.cn/qudongdashi/index.html)                                  | [下载渠道](https://www.423down.com/9157.html)                                   |
| HWiNFO             | 功能很齐全的硬件规格监测工具 | [官网地址](https://www.hwinfo.com)                                                        |                                                                                 |
| AIDA64             | 全球 No.1 的硬件识别         | [官网地址](https://www.aida64.com)                                                        | [下载渠道](https://www.423down.com/887.html)                                    |
| Samsung Magician   | 三星固态硬盘管理工具         | [官网地址](https://www.samsung.com/semiconductor/minisite/ssd/product/consumer/magician/) | [下载渠道](https://semiconductor.samsung.com/consumer-storage/support/tools/)   |
| WDC Dashboard      | 西数固态硬盘管理工具         | [官网地址](https://support-en.wd.com/app/products/product-detailweb/p/1457#WD_downloads)  | [下载渠道](https://wddashboarddownloads.wdc.com/wdDashboard/DashboardSetup.exe) |
| 罗技 Logi Options+ | 罗技管理软件                 | [驱动地址](https://www.logitech.com.cn/zh-cn/software/logi-options-plus.html)             | [离线安装](https://prosupport.logi.com/hc/zh-cn/articles/10991109278871)        |

| 软件           | 描述                                                 | 官网地址                                                                        | 下载渠道                                           |
| :------------- | :--------------------------------------------------- | :------------------------------------------------------------------------------ | :------------------------------------------------- |
| 7-Zip          | 有极高压缩比的开源压缩软件                           | [官网地址](https://www.7-zip.org/)                                              |                                                    |
| 360 压缩       | 压缩格式多 免费无广告                                | [官网地址](https://yasuo.360.cn)                                                |                                                    |
| QQ 拼音输入法  | 比搜狗好的太多 主要没广告                            | [官网地址](http://qq.pinyin.cn)                                                 |                                                    |
| SwitchHosts    | 快速切换不同的 hosts 设置、编辑 hosts 文件           | [官网地址](https://github.com/oldj/SwitchHosts)                                 |                                                    |
| TrafficMonitor | 网速监控悬浮窗软件 可以显示当前网速 CPU 及内存利用率 | [官网地址](https://github.com/zhongyang219/TrafficMonitor)                      |                                                    |
| Bing Wallpaper | 一次浏览一张照片来探索世界                           | [官网地址](https://www.microsoft.com/zh-cn/bing/bing-wallpaper?rtc=1#primaryR2) |                                                    |
| PowerToys      | 自定义 Windows 的实用工具                            | [官网地址](https://docs.microsoft.com/zh-cn/windows/powertoys/)                 | [下载渠道](https://github.com/microsoft/PowerToys) |
| Snipaste       | 一款「截图 + 贴图」的工具                            | [官网地址](https://www.snipaste.com/)                                           |                                                    |
| Bandicam       | 一款简单好用的录屏软件                               | [官网地址](https://www.bandicam.cn/)                                            | [下载渠道](https://www.423down.com/2119.html)      |
| Ditto          | 免费开源的剪贴板增强软件                             | [官网地址](https://ditto-cp.sourceforge.io)                                     |                                                    |
| Everything     | 基于名称快速定位文件和文件夹                         | [官网地址](https://www.voidtools.com/zh-cn/)                                    |                                                    |
| uTools         | 你的生产力工具集 自由集成丰富插件                    | [官网地址](https://u.tools)                                                     |                                                    |
| 互传           | 零流量、极速/多平台                                  | [官网地址](https://es.vivo.com.cn/)                                             |                                                    |
| 钱迹           | 个人财务管理 发现记账的乐趣 全平台支持               | [官网地址](https://www.qianjiapp.com/)                                          |                                                    |

| 软件       | 描述                                        | 官网地址                                         | 下载渠道 |
| :--------- | :------------------------------------------ | :----------------------------------------------- | :------- |
| Arc        | 未来的浏览器                                | [官网地址](https://arc.net/)                     |          |
| Edge       | 新界面更加清爽现代化                        | [官网地址](https://www.microsoft.com/zh-cn/edge) |          |
| Edge-dev   | 新界面更加清爽现代化                        | [官网地址](https://www.microsoft.com/zh-cn/edge) |          |
| Chrome     | 最强的浏览器 没有对手的存在                 | [官网地址](https://www.google.cn/chrome/)        |          |
| Firefox    | 号称最快的浏览器 用的还行                   | [官网地址](https://www.firefox.com.cn)           |          |
| 奔跑的奶酪 | 提供 Edge Chrome Firefox 各个平台增强绿色版 | [官网地址](https://www.runningcheese.com/)       |          |

| 软件               | 描述                               | 官网地址                              | 下载渠道 |
| :----------------- | :--------------------------------- | :------------------------------------ | :------- |
| 迅雷               | 更快 但不止于快                    | [官网地址](https://dl.xunlei.com)     |          |
| BitTorrent Tracker | 全网热门 BitTorrent Tracker 列表！ | [官网地址](https://trackerslist.com/) |          |

| 软件     | 描述                                 | 官网地址                                           | 下载渠道 |
| :------- | :----------------------------------- | :------------------------------------------------- | :------- |
| 百度网盘 | 基本必须下载的网盘 主要资源多        | [官网地址](http://pan.baidu.com/download)          |          |
| 坚果云   | 帮助企业中的变革者改善工作效率和方法 | [官网地址](https://www.jianguoyun.com/s/downloads) |          |

| 软件             | 描述                                                         | 官网地址                                                  | 下载渠道                                      |
| :--------------- | :----------------------------------------------------------- | :-------------------------------------------------------- | :-------------------------------------------- |
| Microsoft Office | 微软 Office 兼容性最好的                                     | [官网地址](https://www.microsoft.com/zh-cn/microsoft-365) | [下载渠道](https://otp.landian.vip/zh-cn/)    |
| WPS              | 免费小巧 购买会员就没有广告了                                | [官网地址](https://www.wps.cn)                            | [下载渠道](https://www.423down.com/8890.html) |
| iSlide           | 基于 PPT 的插件工具 注意需要付费                             | [官网地址](https://www.islide.cc/)                        |                                               |
| 欧路词典         | 权威的英语词典软件 英语学习者必备的工具                      | [官网地址](https://www.eudic.net/v4/en/app/eudic)         |                                               |
| XMind            | 全功能的思维导图和头脑风暴软件                               | [官网地址](https://www.xmind.cn)                          | [下载渠道](https://www.423down.com/9212.html) |
| 亿图图示         | 60 余种办公绘图类型 流程图 架构图 工业设计 图文混排 一软搞定 | [官网地址](https://www.edrawsoft.cn/)                     | [下载渠道](https://www.423down.com/8077.html) |
| 为知笔记         | 大脑是用来思考的 记录的事情交给我们                          | [官网地址](https://www.wiz.cn/zh-cn/wiznew.html)          |                                               |
| 思源笔记         | 思源笔记是一款隐私优先的个人知识管理系统                     | [官网地址](https://b3log.org/siyuan/)                     |                                               |
| VNote            | 一个舒适的笔记平台                                           | [官网地址](https://github.com/vnotex/vnote)               |                                               |

| 软件         | 描述                         | 官网地址                                          | 下载渠道                                                 |
| :----------- | :--------------------------- | :------------------------------------------------ | :------------------------------------------------------- |
| QQ           | I'm QQ - 每一天 乐在沟通     | [官网地址](https://im.qq.com)                     |                                                          |
| 微信         | 微信 是一个生活方式          | [官网地址](https://weixin.qq.com)                 |                                                          |
| 网易邮箱大师 | 高效强大的全平台邮箱客户端   | [官网地址](https://mail.163.com/dashi/index.html) |                                                          |
| 腾讯会议     | 腾讯会议,会开会              | [官网地址](https://meeting.tencent.com/)          |                                                          |
| Zoom         | 视频会议、云电话、网络研讨会 | [官网地址](https://www.zoom.us/)                  | [下载渠道](https://www.zoom.us/download#client_4meeting) |

| 软件    | 描述                                                         | 官网地址                                                  | 下载渠道 |
| :------ | :----------------------------------------------------------- | :-------------------------------------------------------- | :------- |
| Listen1 | One for all free music in China                              | [官网地址](https://listen1.github.io/listen1/)            |          |
| MPV     | 高手推荐的跨平台全能视频播放器！开源、简约、键盘流、配置灵活 | [官网地址](https://mpv.io/)                               |          |
| VLC     | 是一款自由、开源的跨平台多媒体播放器                         | [官网地址](https://www.videolan.org/vlc/index.zh_CN.html) |          |

| 软件        | 描述                         | 官网地址                              | 下载渠道                                         |
| :---------- | :--------------------------- | :------------------------------------ | :----------------------------------------------- |
| Adobe       | Adobe 正通过数字体验改变世界 | [官网地址](https://www.adobe.com/cn/) | [哔哩主页](https://space.bilibili.com/252157636) |
| 2345 看图王 | 一款超好用的看图软件         | [官网地址](https://pic.2345.cc)       | [下载渠道](https://www.423down.com/4111.html)    |

| 软件  | 描述                                       | 官网地址                              | 下载渠道                                                                                                            |
| :---- | :----------------------------------------- | :------------------------------------ | :------------------------------------------------------------------------------------------------------------------ |
| Adobe | Adobe 正通过数字体验改变世界               | [官网地址](https://www.adobe.com/cn/) | [哔哩主页](https://space.bilibili.com/252157636)<br>[微博大咖](https://weibo.com/vposy?profile_ftype=1&is_all=1#_0) |
| 剪映  | 全能易用的桌面端剪辑软件-轻而易剪 上演大幕 | [官网地址](https://www.capcut.cn/)    |                                                                                                                     |


| 软件  | 描述                         | 官网地址                              | 下载渠道                                         |
| :---- | :--------------------------- | :------------------------------------ | :----------------------------------------------- |
| Adobe | Adobe 正通过数字体验改变世界 | [官网地址](https://www.adobe.com/cn/) | [哔哩主页](https://space.bilibili.com/252157636) |
| Axure | 专业的快速原型设计工具       | [官网地址](https://www.axure.com.cn/) |                                                  |

| 软件       | 描述                                                                                                      | 官网地址                                                                              | 下载渠道 |
| :--------- | :-------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------ | :------- |
| VirtualBox | VirtualBox is a powerful x86 and AMD64/Intel64 virtualization product for enterprise as well as home use. | [官网地址](https://www.virtualbox.org/)                                               |          |
| VMware     | Develop and Test for Any Platform With VMware Desktop Hypervisors                                         | [官网地址](https://www.vmware.com/products/desktop-hypervisor/workstation-and-fusion) |          |

| 软件                 | 描述                   | 官网地址                                                             | 下载渠道 |
| :------------------- | :--------------------- | :------------------------------------------------------------------- | :------- |
| Xmanager Power Suite | 性能驱动的网络连接方案 | [官网地址](https://www.xshell.com/zh/xmanager-power-suite-download/) |          |
| 向日葵               | 提供安全顺畅的远程体验 | [官网地址](https://sunlogin.oray.com/download)                       |          |
| ToDesk               | 不一样的远控体验       | [官网地址](https://www.todesk.com/download.html)                     |          |

| 软件             | 描述                                                        | 官网地址                                  | 下载渠道                                |
| :--------------- | :---------------------------------------------------------- | :---------------------------------------- | :-------------------------------------- |
| Spring_STS       | 定制版的 Eclipse 专为 Spring 开发定制的                     | [官网地址](https://spring.io/tools)       |                                         |
| Microsoft_VSCode | 免费开源的现代化轻量级代码编辑器 支持几乎所有主流的开发语言 | [官网地址](https://code.visualstudio.com) |                                         |
| JetBrains_All    | 完整的开发人员工具包                                        | [官网地址](https://www.jetbrains.com)     | [下载渠道](https://www.exception.site/) |
| DCloud_HBuilderX | 轻量编辑器和强大 IDE 的完美结合体                           | [官网地址](https://www.dcloud.io)         |                                         |

| 软件      | 描述                                             | 官网地址                                                        | 下载渠道                                      |
| :-------- | :----------------------------------------------- | :-------------------------------------------------------------- | :-------------------------------------------- |
| EditPlus  | Text editor with FTP, FTPS and sftp capabilities | [官网地址](https://www.editplus.com)                            | [下载渠道](https://www.423down.com/1689.html) |
| Notepad++ | 免费的强大文本编辑器                             | [官网地址](https://notepad-plus-plus.org)                       |                                               |
| PDManer   | 数据库建模                                       | [官网地址](https://gitee.com/robergroup/pdmaner)                |                                               |
| Navicat   | 数据库开发工具                                   | [官网地址](https://www.navicat.com.cn/download/navicat-premium) | [下载渠道](https://www.modb.pro/db/571136)    |
| Postman   | API 开发和测试的工具                             | [官网地址](https://www.postman.com/)                            |                                               |
| Apifox    | API 设计、开发、测试一体化协作平台               | [官网地址](https://www.apifox.cn/)                              |                                               |

"""

# 将 Markdown 表格转换为 DataFrame
df = pd.read_csv(StringIO(markdown_table), sep="|", skipinitialspace=True, header=0, index_col=0)
# df = df.drop(df.columns[-1], axis=1)
df = df[~df.apply(lambda row: row.astype(str).str.contains("---").any(), axis=1)]

# 将 DataFrame 转换为 CSV
csv_output = df.to_csv(index=False)
print(csv_output)
