from datetime import timedelta
from dateutil.relativedelta import relativedelta

from pyforms.basewidget import segment

from pyforms_web.widgets.django import ModelFormWidget


class ContractCreateFormWidget(ModelFormWidget):

    FIELDSETS = [
        'h3:Identification',
        segment(
            ('contract_ref','supervisor'),
            ('person', 'contract_warningemail')
        ),
        'h3:Contract conditions',
        segment(
            ('contract_start', 'contract_duration',
             'contract_duration_additional_days', 'contract_end'),
            ('contract_salary', ),
            ('contract_socialsecuritypaid', 'contract_socialsecurity'),
            ('contract_socialsecuritystart', 'contract_socialsecurityend')
        ),
        'h3:Function',
        segment(
            'position',
            'contract_fellowshipref',
            'typeoffellowship'
        ),
        segment(
            'contract_scientificdesc',
            'contract_notes',
            css='secondary'
        ),
    ]

    READ_ONLY = ['contract_end']

    # AUTHORIZED_GROUPS = ['superuser', settings.APP_PROFILE_HR_PEOPLE]

    @classmethod
    def has_permissions(cls, user):
        from .contracts_list import ContractsListWidget
        return ContractsListWidget.has_permissions(user)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.contract_start.changed_event = self.__update_end_date
        self.contract_duration.changed_event = self.__update_end_date
        self.contract_duration_additional_days.changed_event = self.__update_end_date

    def __update_end_date(self):
        try:
            days = 0 if not self.contract_duration_additional_days.value else self.contract_duration_additional_days.value
            self.contract_end.value = (self.contract_start.value + relativedelta(months=self.contract_duration.value, days=days) - timedelta(days=1))
        except:
            self.contract_end.value = ''


    def update_object_fields(self, obj):
        self.__update_end_date()
        obj.contract_end = self.contract_end.value
        res = super().update_object_fields(obj)
        return res