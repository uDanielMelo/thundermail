import resend
from django.conf import settings


def build_unsubscribe_footer(unsubscribe_url: str) -> str:
    return f"""
    <div style="margin-top:40px;padding-top:20px;border-top:1px solid #e5e7eb;text-align:center;font-family:sans-serif;">
        <p style="font-size:12px;color:#9ca3af;margin:0;">
            Voce esta recebendo este e-mail pois se cadastrou em nossa lista.<br>
            <a href="{unsubscribe_url}" style="color:#6b7280;text-decoration:underline;">
                Cancelar inscricao
            </a>
        </p>
    </div>
    """


def send_campaign_email(
    to: list,
    subject: str,
    body: str,
    from_email: str = None,
    reply_to: str = None,
    unsubscribe_url: str = None,
    user=None,
):
    # Usa configurações do usuário se disponível
    api_key = settings.RESEND_API_KEY
    default_from = getattr(settings, 'RESEND_FROM_EMAIL', 'contato@thundermail.com.br')

    if user:
        try:
            from apps.accounts.models import UserSettings
            user_settings = UserSettings.objects.get(user=user)
            if user_settings.resend_api_key:
                api_key = user_settings.resend_api_key
            if user_settings.resend_from_email:
                default_from = user_settings.resend_from_email
        except Exception:
            pass

    resend.api_key = api_key

    if from_email is None:
        from_email = default_from

    if unsubscribe_url:
        body = body + build_unsubscribe_footer(unsubscribe_url)

    params = {
        "from": from_email,
        "to": to,
        "subject": subject,
        "html": body,
    }

    if reply_to:
        params["reply_to"] = reply_to

    if unsubscribe_url:
        params["headers"] = {
            "List-Unsubscribe": f"<{unsubscribe_url}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        }

    try:
        response = resend.Emails.send(params)
        return {"success": True, "id": response["id"]}
    except Exception as e:
        print(f"ERRO AO ENVIAR: {str(e)}")
        return {"success": False, "error": str(e)}