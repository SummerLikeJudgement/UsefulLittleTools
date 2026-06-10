import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
import os
from datetime import datetime
import platform
import time
from dotenv import load_dotenv
import json

# --- 加载环境变量 ---
load_dotenv()

# --- 配置区（从.env读取）---
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.163.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
AUTH_CODE = os.getenv('AUTH_CODE')

# 从环境变量读取附件路径（JSON数组格式）
attachments_str = os.getenv('ATTACHMENTS', '[]')
try:
    ATTACHMENTS = json.loads(attachments_str)
except json.JSONDecodeError:
    print("⚠️ 附件路径解析失败，请检查.env中的ATTACHMENTS格式")
    ATTACHMENTS = []

# --- 邮件模板配置 ---
# 从环境变量读取模板文件路径，默认为当前目录下的 mail_template.html
template_file_path = os.getenv('MAIL_TEMPLATE_FILE', './mail_template.html')

# 尝试从文件读取模板，失败则停止程序
try:
    with open(template_file_path, 'r', encoding='utf-8') as f:
        MAIL_TEMPLATE = f.read()
    print(f"✅ 成功加载邮件模板：{template_file_path}")
except FileNotFoundError:
    print(f"❌ 错误：邮件模板文件 {template_file_path} 未找到")
    print("请确保模板文件存在，或在.env中正确配置MAIL_TEMPLATE_FILE路径")
    exit(1)
except Exception as e:
    print(f"❌ 错误：加载邮件模板失败 - {e}")
    exit(1)

MIME_TYPES = {
    '.pdf': ('application', 'pdf'),
    '.jpg': ('image', 'jpeg'),
    '.jpeg': ('image', 'jpeg'),
    '.png': ('image', 'png'),
    '.docx': ('application', 'vnd.openxmlformats-officedocument.wordprocessingml.document')
}


def add_attachment(msg, file_path):
    """添加附件，自动处理中文文件名，返回是否成功"""
    try:
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            file_data = f.read()

        ext = os.path.splitext(filename)[1].lower()
        maintype, subtype = MIME_TYPES.get(ext, ('application', 'octet-stream'))

        part = MIMEBase(maintype, subtype)
        part.set_payload(file_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        f'attachment; filename="{Header(filename, "utf-8").encode()}"')
        msg.attach(part)
        print(f'   已添加附件：{filename}')
        return True
    except Exception as e:
        print(f'   ❌ 附件添加失败 {file_path}: {e}')
        return False


def check_attachments():
    """检查所有附件文件是否存在且可读，返回(是否全部可用, 失败列表)"""
    failed_attachments = []
    for path in ATTACHMENTS:
        if not os.path.exists(path):
            failed_attachments.append(f"文件不存在: {path}")
        elif not os.access(path, os.R_OK):
            failed_attachments.append(f"文件不可读: {path}")
        else:
            # 尝试打开文件验证可读性
            try:
                with open(path, 'rb') as f:
                    f.read(1)
            except Exception as e:
                failed_attachments.append(f"文件无法读取: {path} - {e}")

    if failed_attachments:
        print(f"\n⚠️ 附件检查失败，以下附件存在问题：")
        for fail in failed_attachments:
            print(f"   - {fail}")
        return False, failed_attachments
    return True, []


def send_email(email, teacher_name, degree_type, research_interest,
               representative_works, paper_appreciation=""):
    """构建邮件并发送，如果附件添加失败则返回False"""

    # 先检查附件文件是否存在
    attachments_ok, failed_list = check_attachments()
    if not attachments_ok:
        print(f'   ❌ 附件问题，停止发送邮件给 {teacher_name}老师')
        return False

    # 格式化论文引用
    paper_text = ""
    if paper_appreciation.strip():
        paper_text = f'　　{paper_appreciation.strip().replace(chr(10), "<br>")}<br>'

    # 自动获取当前日期（不补零）
    now = datetime.now()
    if platform.system() == 'Windows':
        current_date = f'{now.year}年{now.month}月{now.day}日'
    else:
        current_date = now.strftime('%Y年%-m月%-d日')

    # 填充模板
    mail_content = MAIL_TEMPLATE.format(
        teacher_name=teacher_name,
        degree_type=degree_type,
        research_interest=research_interest,
        representative_works=representative_works,
        current_date=current_date,
        paper_appreciation=paper_text
    )

    # 构建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header('27保研自荐_俞骞_华东师范大学', 'utf-8').encode()
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg.attach(MIMEText(mail_content, 'html', 'utf-8'))

    # 添加附件，如果有任何一个失败则放弃发送
    attachment_success = True
    for path in ATTACHMENTS:
        if not add_attachment(msg, path):
            attachment_success = False
            break  # 一旦有附件添加失败，立即停止

    if not attachment_success:
        print(f'   ❌ 附件添加失败，停止发送邮件给 {teacher_name}老师')
        return False

    # 发送
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, AUTH_CODE)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        print(f'✅ 成功发送至 {email} ({teacher_name}老师)')
        return True
    except Exception as e:
        print(f'❌ 发送失败 {email}: {e}')
        return False


# --- 主程序 ---
if __name__ == '__main__':
    # 验证必要的配置是否存在
    if not SENDER_EMAIL or not AUTH_CODE:
        print("❌ 错误：请在.env文件中配置SENDER_EMAIL和AUTH_CODE")
        exit(1)

    recipients = [
        {
            "email": "example@mail.com",
            "teacher_name": "xxx",
            "degree_type": "硕士研究生",
            "research_interest": "金融人工智能",
            "representative_works": "",
            "paper_appreciation": ""
        },
    ]

    total = len(recipients)
    success_count = 0
    fail_count = 0

    for i, r in enumerate(recipients, 1):
        print(f'\n[{i}/{total}] 正在处理 {r["teacher_name"]}老师...')

        # 只调用一次 send_email，保存返回结果
        result = send_email(**r)

        if result:
            success_count += 1
        else:
            fail_count += 1

        # 只有成功发送后才等待，且只有不是最后一封时才等待
        if i < total and result:
            print(f'等待15秒后发送下一封...')
            time.sleep(15)

    print("\n" + "=" * 50)
    print(f'全部处理完成！成功发送 {success_count} 封，失败 {fail_count} 封。')