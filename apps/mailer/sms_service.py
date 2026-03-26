def send_sms(to: str, message: str, user=None):
    try:
        if user:
            from apps.accounts.models import UserSettings
            settings = UserSettings.objects.get(user=user)
            account_sid = settings.twilio_account_sid
            auth_token = settings.twilio_auth_token
            from_number = settings.twilio_phone_number
        else:
            return {"success": False, "error": "Credenciais Twilio nao configuradas."}

        if not account_sid or not auth_token or not from_number:
            return {"success": False, "error": "Configure o Twilio nas configuracoes."}

        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to
        )
        return {"success": True, "sid": msg.sid}

    except Exception as e:
        print(f"ERRO SMS: {str(e)}")
        return {"success": False, "error": str(e)}