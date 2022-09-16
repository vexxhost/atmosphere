import kopf


@kopf.on.event("secret", field="metadata.name", value="atmosphere-config")
def secret_event_handler(body, **kwargs):
    print(body)
