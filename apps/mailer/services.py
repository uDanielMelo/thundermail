import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY


def send_campaign_email(to: list, subject: str, body: str, from_email: str = None, reply_to: str = None):
    if from_email is None:
        from_email = "onboarding@resend.dev"

    params = {
        "from": from_email,
        "to": to,
        "subject": subject,
        "html": body,
    }

    if reply_to:
        params["reply_to"] = reply_to

    try:
        response = resend.Emails.send(params)
        return {"success": True, "id": response["id"]}
    except Exception as e:
        print(f"ERRO AO ENVIAR: {str(e)}")
        return {"success": False, "error": str(e)}