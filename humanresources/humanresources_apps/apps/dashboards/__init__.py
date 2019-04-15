from django.utils import timezone
import datetime

from django.conf import settings
from confapp import conf

from pyforms.basewidget import BaseWidget
from pyforms.controls import ControlQueryList
from pyforms.controls import ControlQueryCombo

from humanresources.models import Contract
from research.models import Group as ResearchGroup

class ExpiringContracts(BaseWidget):


    UID = 'expiring-contracts'
    TITLE = 'Expiring contracts'

    LAYOUT_POSITION = conf.ORQUESTRA_APPEND_HOME

    CSS = 'mini'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._list = ControlQueryList(
            'List', 
            list_display=[
                'person',
                'contract_ref',
                'contract_end'
            ]
        )

        self._group = ControlQueryCombo(
            'Group', 
            queryset=ResearchGroup.objects.all().order_by('group_name'),
            display_column='group_name',
            changed_event=self.__reload_contracts,
            allow_none=True
        )

        self.formset = ['_group','_list']


        self.__reload_contracts()


    def __reload_contracts(self):

        end_date = timezone.now().date() + datetime.timedelta(settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE )
        
        contracts = Contract.objects.all()
        contracts = contracts.extra(where=[
            "ADDDATE(ADDDATE(contract_start, INTERVAL contract_duration MONTH), INTERVAL contract_duration_additional_days-1 DAY) BETWEEN '{0}' AND '{1}'".format(
                timezone.now().date(), 
                end_date
            )
        ])
        contracts = contracts.filter(contract_warningemail=True) # alert only the contracts with the flag to send warning emails
        contracts = contracts.filter(contract_start__lte = timezone.now().date())
        contracts = contracts.filter(contract_end__gte = timezone.now().date())

        if self._group.value:
            group = ResearchGroup.objects.get(pk=self._group.value)
            contracts = contracts.filter(person__group=group)
        
        contracts.order_by('contract_end')
        self._list.value = contracts