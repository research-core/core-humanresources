from datetime import timedelta
from dateutil.relativedelta import relativedelta

from pyforms.basewidget import segment

from pyforms_web.widgets.django import ModelFormWidget


class ContractCreateFormWidget(ModelFormWidget):

    FIELDSETS = [
        'h3:Identification',
        segment(
            ('ref','supervisor'),
            ('person', 'warn_when_ending')
        ),
        'h3:Contract conditions',
        segment(
            ('start', 'months_duration',
             'days_duration', 'end'),
            ('salary', ),
            ('socialsecurity_pay', 'socialsecurity_from'),
            ('socialsecurity_start', 'socialsecurity_end')
        ),
        'h3:Function',
        segment(
            'position',
            'fellowship_ref',
            'fellowship_type'
        ),
        segment(
            'description',
            'notes',
            css='secondary'
        ),
    ]

    READ_ONLY = ['end']

    # AUTHORIZED_GROUPS = ['superuser', settings.APP_PROFILE_HR_PEOPLE]

    @classmethod
    def has_permissions(cls, user):
        from .contracts_list import ContractsListWidget
        return ContractsListWidget.has_permissions(user)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.start.changed_event = self.__update_end_date
        self.months_duration.changed_event = self.__update_end_date
        self.days_duration.changed_event = self.__update_end_date

    def __update_end_date(self):
        try:
            days = 0 if not self.days_duration.value else self.days_duration.value
            self.end.value = (self.start.value + relativedelta(months=self.months_duration.value, days=days) - timedelta(days=1))
        except:
            self.end.value = ''


    def update_object_fields(self, obj):
        self.__update_end_date()
        obj.end = self.end.value
        res = super().update_object_fields(obj)
        return res