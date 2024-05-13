from django.apps import AppConfig
from django.db.models import signals


class JuntagricoAssignmentRequestAppconfig(AppConfig):
    name = "juntagrico_assignment_request"
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from juntagrico.util import addons
        addons.config.register_version(self.name)

        # Connect signals
        from juntagrico_assignment_request import models, hack
        from juntagrico.entity.jobs import JobType, RecuringJob, Assignment
        signals.pre_save.connect(models.AssignmentRequest.pre_save, sender=models.AssignmentRequest)
        signals.post_save.connect(hack.post_save_job_type, sender=JobType)
        signals.post_save.connect(hack.post_save_recuringjob, sender=RecuringJob)
        signals.pre_save.connect(hack.pre_save_assignment, sender=Assignment)

        #############################################
        # Hide automatically generated jobs and types
        # in admin by monkey patching
        from juntagrico.admins.job_admin import JobAdmin
        from juntagrico.admins.job_type_admin import JobTypeAdmin

        def get_job_type_queryset(self, request):
            return original_get_job_type_queryset(self, request).exclude(
                recuringjob__assignment__assignmentrequest__isnull=False)

        def get_job_queryset(self, request):
            return original_get_job_queryset(self, request).exclude(
                assignment__assignmentrequest__isnull=False)

        original_get_job_type_queryset = JobTypeAdmin.get_queryset
        JobTypeAdmin.get_queryset = get_job_type_queryset
        original_get_job_queryset = JobAdmin.get_queryset
        JobAdmin.get_queryset = get_job_queryset
