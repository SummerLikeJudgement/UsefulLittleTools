# 保研套磁邮件自动发送工具
一个用于批量发送保研自荐邮件的 Python 小工具，支持从excel表格读取导师信息、自动添加附件、个性化填充邮件模板。
默认使用163邮箱，不支持邮件追踪功能。

## 快速开始
1. 安装依赖
```bash
pip install pandas openpyxl python-dotenv
```
2. 配置环境变量：复制 .env.example 为 .env，修改以下配置：
```env
# 邮箱配置
SMTP_SERVER=smtp.163.com      # SMTP服务器
SMTP_PORT=465                 # 端口（SSL）
SENDER_EMAIL=xxx@163.com      # 发件邮箱
AUTH_CODE=your_auth_code      # 邮箱授权码（非登录密码）

# 附件路径（JSON数组格式）
ATTACHMENTS=["简历.pdf", "成绩单.pdf"]

# 导师Excel文件路径
EXCEL_FILE=老师列表.xlsx
START_ROW=1                   # 起始行
END_ROW=10                    # 结束行

# 邮件模板文件路径
MAIL_TEMPLATE_FILE=./mail_template.html
```
3. 准备导师信息（Excel）：需包含三列：老师、邮箱、方向

4. 准备邮件模板：编辑 `mail_template.html` 文件，支持以下占位符：
   - `{teacher_name}` - 老师姓名
   - `{degree_type}` - 学位类型（硕士研究生/博士）
   - `{research_interest}` - 研究方向
   - `{representative_works}` - 代表作说明
   - `{paper_appreciation}` - 老师论文拜读内容
   - `{current_date}` - 当前日期

5. 运行
```bash
# 第一步：提取导师信息后修改autoSend中的导师信息
python profList.py
# 第二步：自动发送邮件
python autoSend.py
```

## 注意事项
- 使用邮箱授权码而非登录密码 
- 附件路径使用双反斜杠 `\\` 或正斜杠 `/` 
- 邮件间隔 15 秒，避免被限流 
- 建议先发送测试邮件确认效果 
- 如需修改邮件模板，直接编辑 `mail_template.html` 文件即可，模板文件必须存在否则程序会终止
- 邮件模板支持 HTML 格式，可使用 `<br>` 换行