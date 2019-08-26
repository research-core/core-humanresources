from datetime import timedelta

import django
from django.db.models import Q
from django.apps import apps
from django.conf import settings
from django.utils.html import format_html
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils    import timezone
from permissions.models import Permission

try:
    # django 2.0
    from django.urls import reverse
except:
    # django 1.6
    from django.core.urlresolvers import reverse

from .contract_queryset import ContractQuerySet

class Contract(models.Model):
    """
    Contract
    ========

    A contract should only be created automatically when a Proposal is
    approved.

    Warnings:



    Represents Private Information about the Person's Contract
    Example: salary, affiliation
    """

    SOCIAL_SECURITY_FROM = [
        ('G', 'Grants'),
        ('I', 'Institution'),
        ('R', 'Running costs')
    ]

    warn_when_ending = models.BooleanField('Warn when the contract is ending', default=True,
                                           help_text='Send an alert warning the end of the contract')
    start           = models.DateField('Start date')
    months_duration = models.IntegerField('Duration', help_text='Months')
    days_duration   = models.IntegerField('Days', help_text='Additional days', default=0)
    end             = models.DateField('End date')
    salary          = models.DecimalField('Monthly Salary', max_digits=15, decimal_places=2)
    fellowship_ref  = models.CharField('Fellowship ref.', max_length=100, blank=True, null=True)
    ref             = models.CharField('Contract ref.', max_length=50, blank=True, null=True, )
    description     = models.TextField('Scientific Work Description', blank=True, null=True, default='')
    notes           = models.TextField('Notes', blank=True, null=True, default='')

    socialsecurity_from  = models.CharField('Soc. Sec', blank=True, null=True, max_length=1, choices=SOCIAL_SECURITY_FROM)
    socialsecurity_pay   = models.NullBooleanField('Paying Social Security', blank=True, null=True, default=None, )
    socialsecurity_start = models.DateField('Soc. Sec. Start date', blank=True, null=True, )
    socialsecurity_end   = models.DateField('Soc. Sec. End date', blank=True, null=True, )

    fellowship_type = models.ForeignKey('humanresources.FellowshipType', blank=True, null=True, verbose_name='Type of fellowship', on_delete=models.CASCADE)
    person          = models.ForeignKey('people.Person', on_delete=models.CASCADE)
    position        = models.ForeignKey('people.Position', null=True, blank=True, on_delete=models.CASCADE)
    supervisor      = models.ForeignKey('people.Person', related_name='contracts_supervisor', null=True, default=None,
                        on_delete=models.CASCADE,
                        limit_choices_to={'auth_user__groups__name': settings.PROFILE_GROUP_RESPONSIBLE, 'active':True})

    objects = ContractQuerySet.as_manager()

    class Meta:
        ordering = ['-end', ]
        verbose_name = "contract"
        verbose_name_plural = "contracts"


    def __str__(self):
        person = self.person
        if self.position is not None:
            return person.name + ' - ' + self.position.name
        else:
            return person.name + ' - No position'

    def can_be_renewed(self):
        today = timezone.now().date()
        return self.is_expiring_soon() or today > self.end
    can_be_renewed.short_description = 'can be renewed'
    can_be_renewed.boolean = True

    def can_be_updated(self):
        # TODO
        pass

    def is_active(self):
        return self.start <= timezone.now().date() <= self.end
    is_active.short_description = 'Active'
    is_active.boolean = True

    def is_expiring_soon(self):
        days_to_end = self.end - timezone.now().date()
        is_expiring = 0 <= days_to_end.days <= settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE
        return self.is_active and is_expiring
    is_expiring_soon.short_description = 'expiring soon'
    is_expiring_soon.boolean = True

    def delete(self):
        from humanresources.models import Payout

        for payout in Payout.objects.filter(contract=self): payout.delete()
        return super().delete()



    def salary2string(self): return "%s %f" % (self.salary)


    def proposal_url(self):
        """
        Link to the Proposal that originated the contract.
        If the contract was updated, this should list the original
        proposal as well as all the others that followed.
        """
        proposals = self.contractproposal_set.order_by('created_on')
        url = ''
        if proposals:
            if proposals.count() > 1:
                url = reverse('admin:humanresources_contractproposal_changelist')
                url += '?contract=%s' % self.pk
            else:
                proposal = proposals.first()
                url = reverse('admin:humanresources_contractproposal_change', args=[proposal.pk])
        return url

    def photo(self):
        if self.person_img:
            return format_html("""<a class='imageLink' target='_blank'href='%s'><img src='%s' width='50px' height='50px'  ></a>""" % (self.person_img.url,self.person_img.url))
        else:
            return ''
    photo.short_description = 'Thumbnail'
    photo.allow_tags = True

    def personuser(self):
        if self.username:
            return django.contrib.auth.models.User.objects.get(username = self.person_username, is_staff=True, is_active=True,)

    # def create_proposal(self, motive):
    #     """
    #     Returns a Proposal object mimicking this contract.

    #     """
    #     print(motive.upper())

    #     new_proposal = ContractProposal(
    #         person=self.person,
    #         contract_start=self.contractproposal_start,
    #         contract_duration=self.contractproposal_duration,
    #         contract_duration_additional_days=self.contractproposal_duration_additional_days,
    #         contract_salary=self.contractproposal_salary,
    #         contract_scientificdesc=self.contractproposal_scientificdesc,
    #         typeoffellowship=self.typeoffellowship,
    #         function=self.function,
    #     )
    #     new_proposal.save()

    #     proposal = self.contractproposal_set.order_by('contractproposal_createdon').first()
    #     proposal.pk = None
    #     proposal.motive = motive

    #     # clean outdated fields

    #     print('got', proposal)
    #     return proposal

    def save(self, *args, **kwargs):
        days = 0 if self.days_duration == None else self.days_duration
        self.end = self.start + relativedelta(months=self.months_duration, days=days) - timedelta(days=1)
        super().save(*args, **kwargs)


    # @staticmethod
    # def get_queryset(request, qs):
    #     # The function will check if the user is a PI.
    #     #If yes, then the user can see all the contracts from his lab. if the user is a super user then
    #     # he will see all the contract s in the database

    #     from people.models import Group as ResearchGroup
    #     user = request.user

    #     if user.is_superuser: return qs
    #     if user.groups.filter(name=settings.PROFILE_HUMAN_RESOURCES).exists(): return qs
    #     if user.groups.filter(name=settings.PROFILE_OSP).exists():
    #         return qs.filter(payout__financeproject__project_code__startswith='2').distinct()

    #     if user.groups.filter( Q(name=settings.PROFILE_GROUP_RESPONSIBLE) |  Q(name=settings.PROFILE_LAB_MANAGER) ).exists():
    #         researchgroup = ResearchGroup.objects.filter(
    #             Q(members__auth_user=user) | Q(person__auth_user=user)
    #         )
    #         auth_groups  = user.groups.filter(name__startswith='GROUP:')
    #         researchgroup = researchgroup.filter( groupdjango__in=auth_groups )
    #         return qs.filter(person__group__in=researchgroup).distinct()

    #     return qs.filter(person__auth_user=user).distinct()






    #### DJANGO 1.6 (Deprecated) #######################

    def contract_proposalpayments(self):
        """
        Return a link "payments" to the "the proposal payments" page where a user with permission
        can read and edit the payments information in the proposal of the selected contract.
        If this contract still dont have payments information, the function
        returns a "Not created yet" label.

        @type  self:    Contract
        @rtype:         link
        @return:        link to the "Payments" page of the proposal of that contract
        """
        from humanresources.models import ContractProposal
        try:
            proposalinfo = ContractProposal.objects.get(contract=self)
            return "<a href='/humanresources/contractproposal/%s/' target='_blank'>GO</a>" % (proposalinfo.pk)
        except ObjectDoesNotExist:
            return "Not set"
    contract_proposalpayments.short_description = 'Contract proposal'
    contract_proposalpayments.allow_tags = True




