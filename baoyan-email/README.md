# 保研套磁邮件自动发送工具

这是一个用于批量发送保研联系邮件的 Python 工具，支持：

- 从 Excel 表格中提取导师姓名、邮箱和研究方向；
- 将导师信息保存为 JSON 格式的 `teacher_info.txt`；
- 从 `teacher_info.txt` 读取收件人；
- 使用 HTML 邮件模板填充导师姓名、学位类型、研究方向和日期；
- 为邮件添加 PDF、图片、Word 等附件；
- 附件配置错误、附件不存在或添加附件失败时，停止发送当前邮件；
- 使用 SMTP_SSL 发送邮件。

本工具不包含邮件追踪、收件确认或发送结果持久化功能。

## 文件说明

```text
baoyan-email/
├── autoSend.py             # 读取收件人并发送邮件
├── profList.py             # 从 Excel 提取导师信息
├── mail_template.html      # 实际使用的邮件模板
├── teacher_info.txt        # profList.py 生成的收件人 JSON 文件
├── .env.example            # 环境变量配置示例
├── requirements.txt        # Python 依赖
└── README.md
```

## 环境要求

- Python 3.12.13
- 已开通 SMTP 服务的邮箱
- Excel 格式的导师名单

## 安装依赖
```bash
pip install -r requirements.txt
```

## 配置环境变量
复制`.env.example`为`.env`，然后编辑

说明：
- `AUTH_CODE` 是邮箱授权码，不是邮箱登录密码；
- `SMTP_PORT=465` 对应当前代码使用的 SSL 连接；
- `ATTACHMENTS` 必须是合法的 JSON 数组；
- Windows 路径建议使用 `/`，例如 `D:/files/resume.pdf`；
- `ATTACHMENTS=[]` 表示不添加附件；
- `EXCEL_FILE` 是导师 Excel 文件路径；
- `START_ROW` 和 `END_ROW` 按 Excel 数据行的 1-based 行号计算，并且包含首尾两行；
- `OUTPUT_FILE` 是 `profList.py` 的输出路径；
- `MAIL_TEMPLATE_FILE` 是 HTML 模板路径；
- `TEACHER_INFO_FILE` 是 `autoSend.py` 读取的收件人 JSON 文件路径。未配置时默认读取 `autoSend.py` 同目录下的 `teacher_info.txt`。

如果从项目根目录执行脚本，建议把模板、收件人和输出文件配置为明确路径，或者先进入 `baoyan-email` 目录

## 准备 Excel 文件

Excel 第一个工作表中需要包含以下列名：`老师`、`邮箱`、`方向`

`profList.py` 会跳过导师姓名或邮箱为空的行。每条有效记录会生成以下字段：

```json
{
    "email": "teacher@example.com",
    "teacher_name": "导师姓名",
    "degree_type": "硕士研究生",
    "research_interest": "研究方向",
    "paper_appreciation": ""
}
```

## 邮件模板

`autoSend.py` 默认读取 `./mail_template.html`。模板使用 Python `str.format()` 填充以下字段：

| 占位符 | 内容 |
| --- | --- |
| `{teacher_name}` | 导师姓名 |
| `{degree_type}` | 学位类型 |
| `{research_interest}` | 导师研究方向 |
| `{paper_appreciation}` | 对导师论文或研究工作的个性化介绍 |
| `{current_date}` | 当前日期 |

## 运行流程
1. 从 Excel 生成收件人文件：执行`python profList.py`。该命令会根据 `.env` 中的 `EXCEL_FILE`、`START_ROW`、`END_ROW` 和 `OUTPUT_FILE`，生成 JSON 格式的 `teacher_info.txt`。
2. 检查收件人文件：`teacher_info.txt` 必须是合法 JSON 数组
3. 发送邮件：执行`python autoSend.py`。多个收件人之间成功发送后等待 15 秒。如果收件人文件不存在、JSON 格式错误、附件路径解析失败、附件不存在或附件添加失败，当前邮件不会发送。


## 提示
- 建议先配置一个测试收件人，确认模板和附件无误后再批量发送；
- 公开仓库中只保留 `.env.example`、通用代码、依赖文件和不含隐私的模板。
