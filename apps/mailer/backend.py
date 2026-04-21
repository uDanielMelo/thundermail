from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
import resend


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        resend.api_key = settings.RESEND_API_KEY
        from_email = getattr(settings, 'RESEND_FROM_EMAIL', 'contato@thundermail.com.br')
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', f'ThunderMail <{from_email}>')

        sent = 0
        for msg in email_messages:
            try:
                body_html = None
                body_text = msg.body

                for content, mimetype in getattr(msg, 'alternatives', []):
                    if mimetype == 'text/html':
                        body_html = content
                        break

                params = {
                    "from": msg.from_email or default_from,
                    "to": list(msg.to),
                    "subject": msg.subject,
                }
                if body_html:
                    params["html"] = body_html
                else:
                    params["text"] = body_text

                if msg.reply_to:
                    params["reply_to"] = list(msg.reply_to)

                resend.Emails.send(params)
                sent += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
        return sent
