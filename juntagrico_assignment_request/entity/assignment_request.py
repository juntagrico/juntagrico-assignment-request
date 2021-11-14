from datetime import datetime, date
import time

from django.db import models
from django.utils.translation import gettext as _
from django.core.validators import MinValueValidator

from juntagrico.entity.member import Member
from juntagrico.entity.jobs import Assignment, ActivityArea, JobType, RecuringJob

from juntagrico.config import Config


class AssignmentRequest(models.Model):
    """
    A request to get an assignment
    """

    JOB_NAME_PREFIX = '_assignment_request_'

    REQUESTED = 'RE'
    REJECTED = 'NO'
    CONFIRMED = 'CO'
    REQUEST_STATUS = [
        (REQUESTED, _('Beantragt')),
        (REJECTED, _('Abgelehnt')),
        (CONFIRMED, _('Bestätigt')),
    ]

    member = models.ForeignKey(Member, verbose_name=Config.vocabulary('member'), on_delete=models.CASCADE,
                               help_text=_("Beantragt von"))
    assignment = models.OneToOneField(Assignment, verbose_name=Config.vocabulary('assignment'),
                                      blank=True, null=True, on_delete=models.PROTECT)
    amount = models.PositiveIntegerField(_('Wert'), default=1, validators=[MinValueValidator(1)],
                                         help_text=_("Wieviele " + Config.vocabulary('assignment_pl') + "?"))
    job_time = models.DateTimeField(_('Geleistet am'), default=datetime.now)
    request_date = models.DateField(_('Beantragt am'), default=date.today, blank=True, null=True)
    response_date = models.DateField(_('Beantwortet am'), blank=True, null=True,
                                     help_text=_("Typischerweise heute"))
    approver = models.ForeignKey(Member, verbose_name=_('Abgesprochen mit'), related_name=_('Referenz'),
                                 blank=True, null=True, on_delete=models.SET_NULL,
                                 help_text=_("An wen soll die Anfrage gesendet werden oder wer hat "
                                             "dich aufgefordert, die Anfrage zu senden?"))

    description = models.TextField(_('Beschreibung'), max_length=1000, default='',
                                   help_text=_("Kurze Beschreibung was du gemacht hat"))
    activityarea = models.ForeignKey(ActivityArea, verbose_name=_('Tätigkeitsbereich'),
                                     blank=True, null=True, on_delete=models.SET_NULL,
                                     help_text=_("Was am besten passt. Ansonsten leer lassen"))
    duration = models.PositiveIntegerField(_('Dauer in Stunden'), default=4)
    location = models.CharField(_('Ort'), max_length=100, blank=True, default='',
                                help_text=_("Optional"))

    status = models.CharField(max_length=2, choices=REQUEST_STATUS, default=REQUESTED,
                              help_text=_('Hier "Bestätigt" auswählen, um die Anfrage anzunehmen'))
    response = models.TextField(_('Antwort'), blank=True, null=True,
                                help_text=_("Rückmeldung an " + Config.vocabulary('assignment') + "-Beantrager. Kann leer bleiben."))

    def __str__(self):
        return _('%s Anfrage #%s') % (Config.vocabulary('assignment'), self.id)

    def is_confirmed(self):
        return self.status == self.CONFIRMED

    def is_rejected(self):
        return self.status == self.REJECTED

    def save(self, **kwargs):
        old_assignment = self.assignment
        super().save(**kwargs)
        # delete assignment object, if request is unconfirmed again
        # this must be done after fully saving the request,
        # because otherwise the assignment is protected by the request
        if old_assignment and not self.assignment:
            self._remove_assignment(old_assignment)

    @classmethod
    def pre_save(cls, sender, instance, **kwds):
        """
        Callback before saving assignment request
        """
        if instance.status == cls.CONFIRMED:
            cls._create_or_update_assignment(instance)
        else:
            instance.assignment = None  # assignment object will be deleted after saving

    def set_activityarea_if_none(self):
        # create/use default activity_area if none specified
        if not self.activityarea:
            self.activityarea, created = ActivityArea.objects.get_or_create(
                name=_('Selbständige Einsätze'),
                defaults={
                    'coordinator': self.approver,
                    'hidden': True
                }
            )

    def get_matching_job_type(self):
        # look for autogenerated job type that matches with request
        values = {x: getattr(self, x) for x in ['activityarea']}
        job_type = JobType.objects.filter(
            name__startswith=self.JOB_NAME_PREFIX,
            **values
        )[:1]
        if job_type:
            return job_type[0]
        # create job type if not exists
        return JobType.objects.create(
            name=f'{self.JOB_NAME_PREFIX}{self.activityarea.id}_{int(time.time())}',  # generate unique job name.
            **values,
            visible=False,
            location='-',  # does not really matter
            default_duration=1,  # overridden in job anyways
            displayed_name=_('Selbständiger Einsatz'),
            description=_('Dies ist ein automatisch erzeugter Einsatz.'),
        )

    def get_matching_job(self):
        # create job with job type if not exists
        return RecuringJob.objects.get_or_create(type=self.get_matching_job_type(),
                                                 time=self.job_time,
                                                 duration_override=self.duration,
                                                 defaults={'slots': 1})[0]

    @classmethod
    def _create_or_update_assignment(cls, instance):
        instance.set_activityarea_if_none()
        # assignment
        if instance.assignment:
            # update if exists:
            # saving the assignment will automatically restore its content. If old job is empty after that, remove it.
            cls._remove_job(instance.assignment.job, instance.assignment.save)

        else:
            # create new if does not exist
            matching_job = instance.get_matching_job()
            if matching_job.free_slots <= 0:
                matching_job.slots += 1 - matching_job.free_slots
                matching_job.save()
            instance.assignment = Assignment.objects.create(member=instance.member,
                                                            job=matching_job, amount=instance.amount)

    @classmethod
    def _remove_assignment(cls, assignment):
        # Delete assignment and job
        cls._remove_job(assignment.job, assignment.delete)

    @classmethod
    def _remove_job(cls, job, before_delete):
        # Delete job, if it has no other assignments
        # the job type is not deleted
        before_delete()
        if job.occupied_places() == 0:
            job.delete()
        elif job.free_slots > 0:  # if job stays, remove emptied slot
            job.slots -= 1

    class Meta:
        verbose_name = _('%s Anfrage') % Config.vocabulary('assignment')
        verbose_name_plural = _('%s Anfragen') % Config.vocabulary('assignment')
        permissions = (
            ('can_confirm_assignments', _('Kann selbständige Arbeitseinsätze bestätigen')),
            ('notified_on_unapproved_assignments', _('Wird über nicht abgesprochene Arbeitseinsätze informiert')),
        )
