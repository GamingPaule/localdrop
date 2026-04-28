from plyer import notification


def notify(title: str, message: str):
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="LocalDrop",
            timeout=6,
        )
    except Exception:
        pass
