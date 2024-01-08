from django.apps import AppConfig


class JuntagricoAssignmentRequestAppconfig(AppConfig):
    name = "juntagrico_assignment_request"
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from juntagrico.util import addons
        addons.config.register_version(self.name)
