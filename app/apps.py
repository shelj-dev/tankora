from django.apps import AppConfig


class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        from .mqtt_client import start_mqtt
        start_mqtt()
