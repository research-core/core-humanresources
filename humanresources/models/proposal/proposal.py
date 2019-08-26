import tempfile
import weasyprint
from datetime import date
from datetime import timedelta

import django
from django.apps import apps
from django.utils.html import format_html
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.core.exceptions import FieldError
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render
from django_weasyprint import WeasyTemplateView
from humanresources.utils import send_mail
from model_utils.models import StatusModel
from model_utils import Choices
from django.urls import reverse

from .proposal_queryset import ProposalQuerySet


class ContractProposal(StatusModel):
    """
    Contract Proposal
    =================

    A contract proposal is used to initiate
    Represents a contract po that has been created by a pi
    """

    STATUS = Choices(
        ('pending', 'Pending'),
        ('printed', 'Printed'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    MOTIVES = Choices(
        ('new', 'New Hire'),
        ('renewal', 'Renewal'),
        ('update', 'Update'),
    )

    motive = models.CharField(
        choices=MOTIVES,
        default=MOTIVES.new,
        max_length=7,
    )

    created_on = models.DateField('Created on', auto_now_add=True)

    person_name  = models.CharField('Person Name', blank=True, null=True, max_length=255, help_text="In case the name is not in the list, fill it here")
    person_email = models.EmailField('Person Email', blank=True, null=True, max_length=255, help_text="Admin will use this to contact the newcomer")
    salary       = models.DecimalField('Monthly stipend / Gross salary', max_digits=15,
                                 decimal_places=2)  #: salary of the Person
    start           = models.DateField('Start date')  #: Start date of the function and affiliation
    months_duration = models.IntegerField('Duration', help_text='Months')
    days_duration   = models.IntegerField('Days', help_text='Additional days', default=0)
    description     = models.TextField('Scientific Work Description', blank=False, null=False, default='', help_text="Short mandatory description")

    person          = models.ForeignKey('people.Person', blank=True, null=True, on_delete=models.CASCADE)
    fellowship_type = models.ForeignKey('FellowshipType', blank=True, null=True, verbose_name='Type of contract', on_delete=models.CASCADE)
    position        = models.ForeignKey('people.Position', null=True, blank=True,  on_delete=models.SET_NULL)
    responsible     = models.ForeignKey('people.Person', blank=True, null=True, verbose_name='Submitted by',
                                         related_name = 'responsible_of_proposals', on_delete=models.SET_NULL )
    closed_on  = models.DateField('Closing date', blank=True, null=True, ) #: Name
    closed_by  = models.ForeignKey('auth.User', blank=True, null=True, verbose_name='Closed by', related_name ='closed_by', on_delete=models.SET_NULL) #: Fk The user that closed that proposal
    contract   = models.ForeignKey('Contract', blank=True, null=True, on_delete=models.SET_NULL)
    supervisor = models.ForeignKey('people.Person', verbose_name='Supervisor', related_name='supervisor_of_proposals',
                                    #limit_choices_to={'auth_user__groups__name': settings.PROFILE_GROUP_RESPONSIBLE},
                                    on_delete=models.SET_NULL, null=True)

    objects = ProposalQuerySet.as_manager()

    class Meta:
        ordering = ['-created_on',]
        verbose_name = "Contract proposal"
        verbose_name_plural = "Contract proposals"


        permissions = (
            ("print_proposal", "Print Proposal"),
            ("can_approve_contract_proposal", "Approve or reject Proposals"),
        )

    def __str__(self):
        name = self.person.full_name if self.person is not None else self.person_name
        return str(name) + ' - ' + (self.position.name if self.position is not None else 'No position')

    def clean(self):

        if self.person is None and (self.person_name is None or len(self.person_name) == 0):
            raise ValidationError('Please enter information about the Person to hire.')


    def personname(self):
        return self.person.full_name if self.person else self.person_name
    personname.short_description = 'Proposal for'
    personname.allow_tags = True

    def end_date(self):
        if self.start is not None:
            duration = 0 if self.months_duration is None else self.months_duration
            days = 0 if self.days_duration == None else self.days_duration
            return self.start + relativedelta(months=duration, days=days) - timedelta(days=1)
        else:
            return None
    end_date.short_description = 'End Date'
    end_date.allow_tags = True

    def save(self, sendemail=False, *args, **kwargs):
        """
        Override the save method to send an email when a new Proposal
        is created.
        """
        if not self.responsible:
            raise ValidationError('This proposal has no person responsible')

        if self._state.adding:  # a new proposal is being created
            sendemail = True

        super().save(*args, **kwargs)

        if sendemail:
            self.send_notification_mail()

    def send_notification_mail(self):
        """Send an email to every user in auth group 'PROFILE: Human resources'
        notifying about this proposal.

        Notifications supported:
            - New
            - Updated # TODO need subject change
        """
        try:
            group = Group.objects.get(name=settings.PROFILE_HUMAN_RESOURCES)
            users = group.user_set.all()
            recipient_list = [
                user.email for user in users if user.email
            ]
        except Group.DoesNotExist:
            recipient_list = []

        # required because pyforms absolute URL includes BASE_URL, but admin doesn't
        if django.VERSION > (2, 0):
            proposal_url = self.get_absolute_url()
        else:
            proposal_url = get_current_site(request=None).domain + self.get_absolute_url()

        message_context = {
            'proposal_url': proposal_url,
            'responsible': self.responsible.full_name,
        }

        subject = 'New contract proposal'

        send_mail(subject, recipient_list, message_context)

    def is_locked(self):
        return self.status in ('submitted', 'approved', 'rejected')

    def status_icon(self):
        d = {
            'pending': '<i class="grey clock icon"></i>',
            'printed': '<i class="blue print icon"></i>',
            'submitted': '<i class="black lock icon"></i>',
            'approved': '<i class="green thumbs up icon"></i>',
            'rejected': '<i class="red thumbs down icon"></i>',
        }

        if self.status == 'approved' and not self.contract:
            d['approved'] = '<i class="yellow exclamation triangle icon"></i>'

        icon = d.get(self.status, '')
        return format_html(f'<div align="center">{icon}</div>')
    status_icon.short_description = 'status'

    def contractproposal_status(self):
        if self.contract is None and self.closed_on:
            return 'Not Approved'
        if self.contract and self.closed_on:
            return 'Approved'
    contractproposal_status.short_description = 'Contract Proposal Status'
    contractproposal_status.allow_tags = True

    def print2pdf(self):
        template = 'humanresources/contract_proposal_pdf_template.html'
        html = render_to_string(template, {'proposal': self})

        filename = tempfile.mktemp()
        with open(filename, "w") as outfile:
            outfile.write(html)

        return weasyprint.HTML(filename).write_pdf()

    # DJANGO 1.6 (Deprecated) #######################

    def printproposal(self):
        if self.pk:
            if not self.closed_by or self.contract:
                return format_html("""<a class='btn btn-alert'
                         href='{0}' target='_blank' >
                         <i class="icon-print icon-black"></i>
                         Print proposal
                      </a>""".format( reverse('print_contract', args=(self.pk,)) ))
            else:
                return "Reopen the proposal to print the contract"
        else:
            return ''
    printproposal.short_description = 'Print proposal'
    printproposal.allow_tags = True

    def contractlink(self):
        if self.pk:
            if self.contract:
                return format_html("""<a class='btn btn-alert'
                         href='{0}' >
                         <i class="icon-remove icon-black"></i>
                         Go to the contract
                      </a>""".format( reverse('approve_contract', args=(self.pk,)) ))
            elif not self.closed_by:
                return format_html("""<a class='btn btn-alert'
                             href='{0}' >
                             <i class="icon-remove icon-black"></i>
                             Create a contract
                          </a>""".format( reverse('approve_contract', args=(self.pk,)) ))
            else:
                return "Reopen the proposal to create the contract"
        else:
            return ''
    contractlink.short_description = 'Contract'
    contractlink.allow_tags = True

    def closeproposal(self):
        if self.pk:
            if not self.contract:
                if self.closed_by:
                    return format_html("""<a class='btn btn-alert'
                                 href='{0}' >
                                 <i class="icon-remove icon-black"></i>
                                 Reopen proposal
                              </a>""".format( reverse('close_contract', args=(self.pk,)) ))
                else:
                    return format_html("""<a class='btn btn-alert'
                                 href='{0}' >
                                 <i class="icon-remove icon-black"></i>
                                 Reject proposal
                              </a>""".format( reverse('close_contract', args=(self.pk,)) ))
            else:
                return "Approved"
        else:
            return ''
    closeproposal.short_description = 'Status'
    closeproposal.allow_tags = True

    def get_absolute_url(self):
        # hack required to have both CORE versions working
        if django.VERSION > (2, 0):
            return settings.NEW_CONTRACT_PROPOSAL_LINK.format(proposal_id=self.pk)
        else:
            return reverse('admin:humanresources_contractproposal_change', args=(self.pk, ))

    # FIXME admin utils should be only in admin

    # def contract_link(self):
    #     if self.contract:
    #         url = reverse('admin:humanresources_contract_change', self.contract.pk)
    #         help_text = 'Contract originated by the approval of this proposal'
    #         return format_html(
    #             f'<a href="{url}" target="_blank" title="{help_text}">'
    #             '<i class="fa fa-file"></i> contract'
    #             '</a>'
    #         )
    #     else:
    #         c = Contract(
    #             person=self.person,
    #         )
    #         url = reverse('admin:humanresources_contract_change', c.pk)
    #         help_text = ''
    #         return format_html(
    #             f'<a href="{url}" target="_blank" title="{help_text}" disabled>'
    #             '<i class="fa fa-file"></i> create contract'
    #             '</a>'
    #         )

    # FIXME remove, moved to utils

    # def print(self):
    #     url = reverse('print_contract', args=(self.pk,))
    #     icon = '<i class="fas fa-print"></i>'
    #     help_text = 'Print the proposal'
    #     link = '<a href="{}" target="_blank" title="{}">{} print</a>'
    #     return format_html(link.format(url, help_text, icon))

    def generate_contract(self, **kwargs):
        """
        Create a Contract based on an approved Proposal.
        """

        Contract = apps.get_model('humanresources', 'Contract')
        Payout   = apps.get_model('humanresources', 'Payout')

        if self.status != 'approved':
            raise ValidationError(
                "Proposal needs to be approved in order to originate a"
                " contract."
            )
        if self.contract:
            raise FieldError("A Contract for this proposal already exists")

        new_contract = Contract(
            person=self.person,
            start=self.start,
            months_duration=self.months_duration,
            days_duration=self.days_duration,
            salary=self.salary,
            description=self.description,
            fellowship_type=self.fellowship_type,
            position=self.position,
        )
        new_contract.save()

        for payment in self.payment_set.all():
            # request by Teresa:
            # Payout end date should not fall beyond end of the current year
            proposal_start = self.start
            proposal_end = self.end_date()
            if proposal_end.year > proposal_start.year:
                proposal_end = date(proposal_start.year, 12, 31)

            payout = Payout(
                contract=new_contract,
                project=payment.project,
                amount=payment.amount,
                start=proposal_start,
                end=proposal_end,
            )
            payout.save(user=kwargs.get('user', None))

        self.contract = new_contract
        self.save()

        return new_contract

    def generate_pdf_view(self, request=None):
        """Returns a PDF view for this proposal."""

        template = 'pdfs/contract_proposal_pdf_template.html'

        context = {
            'proposal': self,

            # FIXME test only
            'motive': 'New Hire',
            'proposal_date': self.created_on.strftime('%b %d, %Y'),
        }

        # FIXME this should be the debug, erase the `not`
        if 'debug' not in request.GET:
            return render(
                request,
                template_name=template,
                context=context,
            )

        return WeasyTemplateView.as_view(
            template_name=template,
            extra_context=context,
        )(request)
