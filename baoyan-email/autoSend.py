import json
import os
import platform
import smtplib
import time
from datetime import datetime
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.163.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
AUTH_CODE = os.getenv("AUTH_CODE")

template_file_path = os.getenv("MAIL_TEMPLATE_FILE", "./mail_template.html")
teacher_info_file_path = os.getenv("TEACHER_INFO_FILE", str(Path(__file__).with_name("teacher_info.txt")))

try:
    with open(template_file_path, "r", encoding="utf-8") as f:
        MAIL_TEMPLATE = f.read()
    print(f"✅ 成功加载邮件模板：{template_file_path}")
except FileNotFoundError:
    print(f"❌ 错误：邮件模板文件 {template_file_path} 未找到")
    print("请确保模板文件存在，或在.env中正确配置MAIL_TEMPLATE_FILE路径")
    raise SystemExit(1)
except Exception as e:
    print(f"❌ 错误：加载邮件模板失败 - {e}")
    raise SystemExit(1)

MIME_TYPES = {
    ".pdf": ("application", "pdf"),
    ".jpg": ("image", "jpeg"),
    ".jpeg": ("image", "jpeg"),
    ".png": ("image", "png"),
    ".docx": ("application", "vnd.openxmlformats-officedocument.wordprocessingml.document"),
}


def load_recipients():
    """从 teacher_info.txt 读取收件人列表。"""
    try:
        with open(teacher_info_file_path, "r", encoding="utf-8") as f:
            recipients = json.load(f)
        if not isinstance(recipients, list):
            raise ValueError("teacher_info.txt 必须是 JSON 数组")
        return recipients
    except FileNotFoundError:
        print(f"❌ 未找到收件人文件：{teacher_info_file_path}")
        return None
    except Exception as e:
        print(f"❌ 读取收件人文件失败：{e}")
        return None


def load_attachment_paths():
    """从环境变量读取附件路径列表。解析失败时返回 None。"""
    attachments_str = os.getenv("ATTACHMENTS", "[]").strip()
    try:
        attachments = json.loads(attachments_str)
        if not isinstance(attachments, list):
            raise ValueError("ATTACHMENTS must be a JSON array")
        return attachments
    except Exception as e:
        print("⚠️ 附件路径解析失败，请检查.env中的ATTACHMENTS格式")
        print(f"   详情: {e}")
        return None


def add_attachment(msg, file_path):
    """添加附件。失败时直接抛出异常。"""
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_data = f.read()

    ext = os.path.splitext(filename)[1].lower()
    maintype, subtype = MIME_TYPES.get(ext, ("application", "octet-stream"))

    part = MIMEBase(maintype, subtype)
    part.set_payload(file_data)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{Header(filename, "utf-8").encode()}"',
    )
    msg.attach(part)
    print(f"   已添加附件：{filename}")


def check_attachments(attachment_paths):
    """检查所有附件文件是否存在且可读。"""
    failed = []
    for path in attachment_paths:
        if not os.path.exists(path):
            failed.append(f"文件不存在: {path}")
        elif not os.access(path, os.R_OK):
            failed.append(f"文件不可读: {path}")
        else:
            try:
                with open(path, "rb") as f:
                    f.read(1)
            except Exception as e:
                failed.append(f"文件无法读取: {path} - {e}")

    if failed:
        print("\n❌ 附件检查失败，以下附件存在问题：")
        for item in failed:
            print(f"   - {item}")
        return False
    return True


def send_email(email, teacher_name, degree_type, research_interest, paper_appreciation=""):
    attachment_paths = load_attachment_paths()
    if attachment_paths is None:
        print(f"   ❌ 附件配置有误，停止发送给 {teacher_name}老师")
        return False

    if not check_attachments(attachment_paths):
        print(f"   ❌ 附件有问题，停止发送给 {teacher_name}老师")
        return False

    paper_text = ""
    if paper_appreciation.strip():
        paper_text = f"　　{paper_appreciation.strip().replace(chr(10), '<br>')}<br>"

    now = datetime.now()
    if platform.system() == "Windows":
        current_date = f"{now.year}年{now.month}月{now.day}日"
    else:
        current_date = now.strftime("%Y年%-m月%-d日")

    mail_content = MAIL_TEMPLATE.format(
        teacher_name=teacher_name,
        degree_type=degree_type,
        research_interest=research_interest,
        current_date=current_date,
        paper_appreciation=paper_text,
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header("27保研自荐_俞骞_华东师范大学", "utf-8").encode()
    msg["From"] = SENDER_EMAIL
    msg["To"] = email
    msg.attach(MIMEText(mail_content, "html", "utf-8"))

    for path in attachment_paths:
        try:
            add_attachment(msg, path)
        except Exception as e:
            print(f"   ❌ 附件添加失败 {path}: {e}")
            print(f"   ❌ 停止发送邮件给 {teacher_name}老师")
            return False

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, AUTH_CODE)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        print(f"✅ 成功发送至 {email} ({teacher_name}老师)")
        return True
    except Exception as e:
        print(f"❌ 发送失败 {email}: {e}")
        return False


if __name__ == "__main__":
    if not SENDER_EMAIL or not AUTH_CODE:
        print("❌ 错误：请在.env文件中配置SENDER_EMAIL和AUTH_CODE")
        raise SystemExit(1)

    recipients = load_recipients()
    if recipients is None:
        raise SystemExit(1)
    if not recipients:
        print(f"❌ 收件人文件为空：{teacher_info_file_path}")
        raise SystemExit(1)

    total = len(recipients)
    success_count = 0
    fail_count = 0

    for i, r in enumerate(recipients, 1):
        print(f"\n[{i}/{total}] 正在处理 {r['teacher_name']}老师...")
        result = send_email(**r)

        if result:
            success_count += 1
        else:
            fail_count += 1

        if i < total and result:
            print("等待15秒后发送下一封...")
            time.sleep(15)

    print("\n" + "=" * 50)
    print(f"全部处理完成！成功发送 {success_count} 封，失败 {fail_count} 封。")
