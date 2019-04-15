from django.apps import AppConfig


class HumanResourcesConfig(AppConfig):
    name = 'humanresources'
    verbose_name = 'Human Resources'

    def ready(self):
        from . import signals  # noqa
