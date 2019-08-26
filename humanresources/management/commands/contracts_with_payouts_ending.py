import os
import sys
import datetime
import django

from pprint import pprint

from django.utils import timezone
from django.conf import settings
from django.contrib.auth import models
from django.core.mail import EmailMessage
from humanresources.models import Payout, Contract, Payout
from people.models import Person
from django.template.loader import render_to_string
from django.db.models import *
from django.core.management.base import BaseCommand

END_DATE = timezone.datetime.today().date() + datetime.timedelta(settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE)
TODAY = timezone.datetime.today().date()
INTERVAL_RANGE = settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE

class Command(BaseCommand):
    help = 'Sends email with payouts ending to the users with the profile PROFILE_EXPIRING_CONTRACTS_OF_MY_GROUP'

    # For each contract in 'contracts' verify if there are
    # no-pay days between 'today' and 'end_date'

    def validate_payouts(self, contracts):
        for contract in contracts:
            marker = [False] * INTERVAL_RANGE

            payouts = Payout.objects.filter(Q(contract=contract) &
                                            ((Q(start__gte=TODAY) & Q(end__lte=END_DATE)) |
                                             (Q(start__lte=TODAY) & Q(end__gte=TODAY)) |
                                             (Q(start__gte=TODAY) & Q(end__gte=END_DATE))
                                            )
                                            ).distinct()
            
            # Verify if there are payouts to cover the next ENDING_CONTRACT_WARNING_N_DAYS_BEFORE days 
            for p in payouts:
                delta = (p.start - TODAY).days

                if delta <= 0:
                    start_at = 0
                else:
                    start_at = delta

                end_at = (p.end - p.start).days
                if end_at > INTERVAL_RANGE - start_at:
                    end_at = INTERVAL_RANGE - start_at

                for x in range(start_at, end_at):
                    marker[x] = True

            # If the contract doesnt cover all days mark it as expiring
            for e in marker:
                if not e:
                    yield contract
                    break


    def contracts_with_payout_expiring(self):
        #Select all the contracts that doesn't have payouts to cover the end of th contract
        contracts = Contract.objects.raw(f"""
                                        select * from humanresources_payout b, humanresources_contract a
                                        where a.id = b.id and
                                        b.end < a.end and
                                        a.end > CURDATE() + INTERVAL {settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE} DAY;
                                        """)
        result = []
        
        # Get contracts without payouts
        for c in Contract.objects.filter(payout=None):
            result.append(c)
        # Get contracts that dont have payouts for the next ENDING_CONTRACT_WARNING_N_DAYS_BEFORE days
        for c in self.validate_payouts(contracts):
            result.append(c)

        return sorted(list(set(result)), key=lambda x: str(x.person))

    def contracts_expiring(self):
        # Select all the contracts that doesn't have payouts to cover the end of th contract
        contracts_expiring = Contract.objects.filter(end__range=[TODAY, END_DATE])

        return sorted(list(set(contracts_expiring)), key=lambda x: str(x.person))

    def handle(self,  *args, **options):
        contracts_with_no_payouts = self.contracts_with_payout_expiring()
        contracts_ending = self.contracts_expiring()

        template = os.path.join('emails', 'contracts_with_payouts_ending.html')
        rendered = render_to_string(template, 
                                    {'contracts_with_no_payouts': contracts_with_no_payouts,
                                     'contracts_ending': contracts_ending,
                                     'link': settings.ENDING_CONTRACT_LINK,
                                     'today': TODAY
                                     })

        send_to = []
        group = models.Group.objects.get(name=settings.PROFILE_EXPIRING_CONTRACTS_AND_PAYOUTS)
        for user in group.user_set.all():
            if user.email:
                send_to.append(user.email)

        msg = EmailMessage(f'Report for the next {settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE} days',
                           rendered, 
                           settings.ENDING_CONTRACT_FROM, 
                           send_to)
        msg.content_subtype = "html"
        msg.send()
