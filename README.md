# Fuchsia Doc 简体中文翻译工具

## 功能
利用 https://translate.google.com/ 自动按照

```markdown
<!--
Original Text
 -->
译文
```

格式进行文档翻译并保存。可以自动跳过代码块。

**注意：本程序仅实现了自动化机器翻译，自动翻译后需要人工核查并调整翻译内容与格式。**

## 使用方法

首先安装依赖库：

```shell
pip install -r requirements.txt
```

安装依赖后即可使用：

```shell
python main.py -i [ipath] -o [opath] -p [proxy]
```
- `-i [ipath]`：<b>（必需）</b>指定输入路径，其中 `[ipath]` 为待翻译英文原文件路径
- `-o [ipath]`：（可选）指定输出路径，其中 `[opath]` 为翻译后文件输出路径。**不指定时覆盖输入文件。**
- `-p [proxy]`：（可选）指定代理地址，其中 `[proxy]` 为代理地址，形如 `a.b.c.d:e` 或 `protocol://a.b.c.d:e`。**不指定时请确保可以直连 https://translate.google.com/ 。**

亦支持长参数。如需了解请参阅源代码，在此不进行赘述。

我使用的 Python 版本为 3.10.5。
