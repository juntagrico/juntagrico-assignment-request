from juntagrico_assignment_request.models import AssignmentRequest

"""
This hack ensures that the jobs from assignment request can not be manipulated.
In the future juntagrico should offer ways to create custom job models in addons and make this hack obsolete.
"""


def bulk_save(elements):
    for element in elements:
        element.save()
        print(f'Resaved {element}')


def post_save_job_type(sender, instance, **kwds):
    """
    As we can not prevent admins from messing with autogenerated job types, we
    re-save all assignment requests. if any relevant part of this job type was changed,
    the requests will create a new matching job type and adapt their jobs to that.
    """
    # get assignment requests that are attached to any assignments of jobs of that job type and re-save them
    bulk_save(AssignmentRequest.objects.filter(
        assignment__job__in=instance.recuringjob_set.filter(assignment__assignmentrequest__isnull=False)
    ))


def post_save_recuringjob(sender, instance, **kwds):
    """
    same idea as post_save_job_type
    """
    # get assignment requests that are attached to any assignments of this job and re-save them
    bulk_save(AssignmentRequest.objects.filter(
        assignment__in=instance.assignment_set.filter(assignmentrequest__isnull=False)
    ))


def pre_save_assignment(sender, instance, **kwds):
    """
    If assignment comes from request, change back values as before saving it
    """
    if not kwds.get('raw', False):
        if hasattr(instance, 'assignmentrequest'):
            ar = instance.assignmentrequest
            instance.member = ar.member
            instance.amount = ar.get_amount()
            instance.job = ar.get_matching_job()
            print(f'restored {instance} using {ar}')
