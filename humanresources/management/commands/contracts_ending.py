import datetime, os
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMessage
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.core.management.base import BaseCommand
from humanresources.models import Contract, ContractProposal
from people.models import Person




class Command(BaseCommand):
    help = 'Sends email with contracts ending to the users with the profile PROFILE_EXPIRING_CONTRACTS_OF_MY_GROUP'

    def get_contracts_expiring(self, end_date, groups):
        """
        Find the contracts ending, from people that belong to specific Django groups.
        """
        if groups:
            contracts = Contract.objects.filter(end__range=[timezone.datetime.today().date(), end_date],
                                                person__group__in=groups)
            # only the contracts marked to receive a warning alert
            contracts = contracts.filter(contract_warningemail=True)
            contracts_expiring = []
            for contract in contracts:
                # Check for each contract, if it exists already a proposal created.
                # if not send a warning email
                start_proposal = contract.end + datetime.timedelta(days=1)
                proposals = ContractProposal.objects.filter(person=contract.person)
                proposals = proposals.filter(start=start_proposal)

                if not proposals.exists():
                    contracts_expiring.append(contract)
                
            # sort and remove duplicated contracts
            return sorted(list(set(contracts_expiring)), key=lambda x: str(x.person))
        else:
            return []




    def handle(self,  *args, **options):
        # Calculate the future date used to filter the expiring contracts.
        end_date = timezone.datetime.today().date() + datetime.timedelta(days=settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE)

        # Get the Django Group that should be notified about the expiring contracts.
        notification_group = Group.objects.get(name=settings.PROFILE_EXPIRING_CONTRACTS_OF_MY_GROUP)

        sent_to_users = []
        for user in notification_group.user_set.all().order_by('username'):
            if user.email:
                send_to = [user.email]
                try:
                    person = Person.objects.get(auth_user=user)
                    researchgroups = person.group_set.all()
                    # calculate the expering contracts belonging to the user groups
                    contracts_ending = self.get_contracts_expiring(end_date, researchgroups)
                    if len(contracts_ending) > 0:
                        template = os.path.join('emails', 'contracts_ending.html')
                        rendered_msg = render_to_string(template, 
                                                        {'contracts_ending': contracts_ending,
                                                         'link': settings.ENDING_CONTRACT_LINK, 'today': timezone.datetime.today().date(),
                                                         'pi': '%s %s' % (user.first_name, user.last_name),
                                                         'deadline': settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE,}
                                                        )

                        # send the email
                        subject = f'CNP CORE ({timezone.datetime.today().date()}): ' \
                                  f'Contracts expiring in the next {settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE} days'
                        msg = EmailMessage(subject, rendered_msg, settings.ENDING_CONTRACT_FROM, send_to)
                        msg.content_subtype = "html"
                        msg.send()
                        sent_to_users.append(str(user))
                except Person.DoesNotExist:
                    pass

        ### Notify the users in the HR profile about witch users were warned ###########
        group = Group.objects.get(name=settings.PROFILE_HUMAN_RESOURCES)
        send_to = [user.email for user in group.user_set.all() if user.email]
        rendered_msg = "This report was sent to:<br/><br/>"+'<br/>'.join( sent_to_users )
        msg = EmailMessage(f'Contracts expiring in the next {settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE} days: sending report',
                           rendered_msg,
                           settings.ENDING_CONTRACT_FROM,
                           send_to)
        msg.content_subtype = "html"
        msg.send()
        #################################################################################