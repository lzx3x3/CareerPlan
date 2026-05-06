"""
邮箱验证码发送模块
支持 SMTP 发送（Gmail/Outlook/QQ邮箱等）
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSender:
    """邮箱发送器"""

    def __init__(self):
        self.smtp_host = os.environ.get('SMTP_HOST', '')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '465'))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_pass = os.environ.get('SMTP_PASS', '')
        self.from_name = os.environ.get('SMTP_FROM_NAME', '职画')
        self.enabled = bool(self.smtp_host and self.smtp_user and self.smtp_pass)

    def send_code(self, to_email: str, code: str) -> bool:
        """发送验证码邮件"""
        if not self.enabled:
            print(f"⚠️ 邮件服务未配置！验证码: {code} -> {to_email}")
            print(f"   请在 .env 文件中配置 SMTP_HOST, SMTP_USER, SMTP_PASS")
            return False

        subject = f"【职画】您的验证码是 {code}"
        html_content = f"""
        <div style="max-width:480px;margin:0 auto;padding:20px;font-family:'Segoe UI',sans-serif;">
            <div style="background:linear-gradient(135deg,#e8381a,#ff6b35);border-radius:16px 16px 0 0;
                        padding:24px;text-align:center;">
                <h2 style="color:white;margin:0;font-size:20px;">🎮 职画</h2>
            </div>
            <div style="background:white;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 16px 16px;
                        padding:30px 24px;">
                <p style="color:#333;font-size:14px;margin-bottom:16px;">您好！您正在登录/注册职画，验证码为：</p>
                <div style="background:#f5f5f5;border-radius:12px;padding:20px;text-align:center;margin:16px 0;">
                    <span style="font-size:32px;font-weight:900;color:#e8381a;letter-spacing:8px;">{code}</span>
                </div>
                <p style="color:#999;font-size:12px;">验证码10分钟内有效，请勿泄露给他人。</p>
            </div>
        </div>
        """

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.smtp_user}>"
            msg['To'] = to_email
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()

            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, to_email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False


# 全局实例
email_sender = EmailSender()
