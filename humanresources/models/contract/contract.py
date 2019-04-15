from datetime import timedelta

from django.db.models import Q
from django.apps import apps
from django.conf import settings
from django.utils.html import format_html
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils    import timezone
from common.models import Permissions

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

    # FIXME clean up fields
    contract_id                     = models.AutoField(primary_key=True) #: ID
    contract_start                  = models.DateField('Start date')              #: Start date of the function and affiliation
    contract_duration               = models.IntegerField('Duration', help_text='Months')
    contract_duration_additional_days = models.IntegerField('Days', help_text='Additional days', default=0)
    contract_end                    = models.DateField('End date') # Temporary
    contract_salary                 = models.DecimalField('Monthly Salary', max_digits=15, decimal_places=2)  #: salary of the Person
    contract_socialsecurity         = models.CharField('Soc. Sec', blank=True, null=True, max_length=4, choices=( ('G','Grants'),('CF','CF'),('CFRC','CF Running costs') ) ) #: Soc. Sec number of a Person
    contract_fellowshipref          = models.CharField('Fellowship ref.', max_length=100, blank=True, null=True,)   #: Scholarship refrences of a Person
    contract_ref                    = models.CharField('Contract ref.', max_length=50, blank=True, null=True,)   #: Contract refrences of a Person
    contract_socialsecuritypaid     = models.NullBooleanField('Paying Social Security', blank=True, null=True, default=None,)
    contract_socialsecuritystart    = models.DateField('Soc. Sec. Start date', blank=True, null=True,)
    contract_socialsecurityend      = models.DateField('Soc. Sec. End date', blank=True, null=True,)
    contract_scientificdesc         = models.TextField('Scientific Work Description', blank=True, null=True, default='')
    contract_notes                  = models.TextField('Notes', blank=True, null=True, default='')
    contract_warningemail           = models.BooleanField('Warn when the contract is ending', default=True, help_text='Send an alert warning the end of the contract')


    typeoffellowship = models.ForeignKey('TypeOfFellowship', blank=True, null=True, verbose_name='Type of fellowship', on_delete=models.CASCADE)
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    financinginst = models.ForeignKey('FinancingInst', verbose_name='Paid by', blank=True, null=True, on_delete=models.CASCADE)

    position = models.ForeignKey(
        to='Position',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    supervisor = models.ForeignKey(
        to='humanresources.Person',
        related_name='supervisor',
        null=True,
        default=None,
        on_delete=models.CASCADE,
        limit_choices_to={'djangouser__groups__name': settings.PROFILE_GROUP_RESPONSIBLE, 'person_active':True},
    )

    objects = ContractQuerySet.as_manager()

    class Meta:
        ordering = ['-contract_end', ]
        verbose_name = "contract"
        verbose_name_plural = "contracts"
        # abstract = True
        app_label = 'humanresources'


    def __str__(self):
        person = self.person
        if self.position is not None:
            return person.name + ' - ' + self.position.name
        else:
            return person.name + ' - No position'

    def can_be_renewed(self):
        today = timezone.now().date()
        return self.is_expiring_soon() or today > self.contract_end
    can_be_renewed.short_description = 'can be renewed'
    can_be_renewed.boolean = True

    def can_be_updated(self):
        # TODO
        pass

    def is_active(self):
        return self.contract_start <= timezone.now().date() <= self.contract_end
    is_active.short_description = 'Active'
    is_active.boolean = True

    def is_expiring_soon(self):
        days_to_end = self.contract_end - timezone.now().date()
        is_expiring = 0 <= days_to_end.days <= settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE
        return self.is_active and is_expiring
    is_expiring_soon.short_description = 'expiring soon'
    is_expiring_soon.boolean = True

    def delete(self):
        from humanresources.models import Payout

        for payout in Payout.objects.filter(contract=self): payout.delete()
        return super().delete()



    def salary2string(self): return "%s %f" % ( self.contract_salary )


    def proposal_url(self):
        """
        Link to the Proposal that originated the contract.
        If the contract was updated, this should list the original
        proposal as well as all the others that followed.
        """
        proposals = self.contractproposal_set.order_by('contractproposal_createdon')
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
        days = 0 if self.contract_duration_additional_days==None else self.contract_duration_additional_days
        self.contract_end = self.contract_start + relativedelta(months=self.contract_duration, days=days) - timedelta(days=1)
        super().save(*args, **kwargs)


    # @staticmethod
    # def get_queryset(request, qs):
    #     # The function will check if the user is a PI.
    #     #If yes, then the user can see all the contracts from his lab. if the user is a super user then
    #     # he will see all the contract s in the database

    #     from research.models import Group as ResearchGroup
    #     user = request.user

    #     if user.is_superuser: return qs
    #     if user.groups.filter(name=settings.PROFILE_HUMAN_RESOURCES).exists(): return qs
    #     if user.groups.filter(name=settings.PROFILE_OSP).exists():
    #         return qs.filter(payout__financeproject__financeproject_code__startswith='2').distinct()

    #     if user.groups.filter( Q(name=settings.PROFILE_GROUP_RESPONSIBLE) |  Q(name=settings.PROFILE_LAB_MANAGER) ).exists():
    #         researchgroup = ResearchGroup.objects.filter(
    #             Q(members__djangouser=user) | Q(person__djangouser=user)
    #         )
    #         djangogroups  = user.groups.filter(name__startswith='GROUP:')
    #         researchgroup = researchgroup.filter( groupdjango__in=djangogroups )
    #         return qs.filter(person__group__in=researchgroup).distinct()

    #     return qs.filter(person__djangouser=user).distinct()






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
            return "<a href='/humanresources/contractproposal/%s/' target='_blank'>GO</a>" % (proposalinfo.contractproposal_id)
        except ObjectDoesNotExist:
            return "Not set"
    contract_proposalpayments.short_description = 'Contract proposal'
    contract_proposalpayments.allow_tags = True




