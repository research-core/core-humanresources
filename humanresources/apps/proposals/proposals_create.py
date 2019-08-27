from django.urls import reverse
from confapp import conf
from django.conf import settings

from pyforms_web.web.middleware import PyFormsMiddleware

from pyforms.basewidget import segment, no_columns
from pyforms.controls import ControlAutoComplete
from pyforms.controls import ControlImg
from pyforms_web.widgets.django import ModelAdminWidget
from pyforms_web.widgets.django import ModelFormWidget

from humanresources.models import ContractProposal
from humanresources.models import Payment
from people.models import Person

import time
from sorl.thumbnail import get_thumbnail

from datetime import timedelta
from dateutil.relativedelta import relativedelta


class CreateContractProposalFormWidget(ModelFormWidget):

    FIELDSETS = [
        (
            segment(
                'h3:IDENTIFICATION OF THE PARTIES',
                ('person', 'supervisor'),
                'info:If the Person is missing from the list, use the '
                'fields below to indicate the name and email contact',
                (
                    'person_name',
                    'person_email',
                ),
                field_css='fourteen wide',
            ),
            segment(
                '_img',
                field_style='max-width:330px;'
            )
        ),
        segment(
            'h3:CONTRACT DETAILS',
            (
                'start',
                'months_duration',
                'days_duration',
                'end_date',
            ),
            (
                'position',
                'fellowship_type',
                'salary',
                ' '
            ),
            'description',
        )
    ]

    @classmethod
    def has_permissions(cls, user):
        from .proposals_list import ContractProposalsListWidget
        return ContractProposalsListWidget.has_permissions(user)

    def __init__(self, *args, **kwargs):

        self._img = ControlImg('Image', label_visible=False)

        super().__init__(*args, **kwargs)

        self.start.changed_event = self.__update_end_date
        self.months_duration.changed_event = self.__update_end_date
        self.days_duration.changed_event = self.__update_end_date

        # Handle situation where Add Form is opened as inline
        if not hasattr(self, 'person'):
            person = Person.objects.get(pk=self.parent_pk)
            self.person = ControlAutoComplete(
                label='Person',
                queryset=Person.objects.all(),
                default=person.pk,
                readonly=True,
            )
            self.__update_image_evt()

        self.person.changed_event = self.__update_image_evt

    def __update_end_date(self):

        try:
            days = 0 if not self.days_duration.value else self.days_duration.value
            self.end_date.value = (self.start.value.date() + relativedelta(months=self.months_duration.value, days=days) - timedelta(days=1))
        except:
            self.end_date.value = ''

    def __update_image_evt(self):
        try:
            person = Person.objects.get(pk=self.person.value)
        except Person.DoesNotExist:
            url = Person.DEFAULT_PICTURE_URL
        else:
            url = person.thumbnail_url('300x300')
        self._img.value = url

    def save_event(self, obj, new_object):
        if new_object:
            user = PyFormsMiddleware.user()
            obj.responsible = user.person
        return super().save_event(obj, new_object)
