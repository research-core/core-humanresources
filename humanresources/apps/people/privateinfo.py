from django.conf import settings

from pyforms.basewidget import segment
from pyforms_web.widgets.django import ModelFormWidget
from pyforms_web.web.middleware import PyFormsMiddleware

from humanresources.models import PrivateInfo


class PrivateInfoFormWidget(ModelFormWidget):
    """
    To be used as inline: `person` field missing
    """

    MODEL = PrivateInfo
    TITLE = 'Private Info'

    FIELDSETS = [
        # 'info:The information provided in the fields below is only shared with the HR department.',
        ('birthcountry', 'birthcity', 'citizenship'),
        segment(
            'h3:Documentation',
            ('iddoc', 'iddoc_number', 'iddoc_expiration'),
            ('nif', 'socialsecurity_number')
        ),
        segment(
            'h3:Health Insurance',
            ('has_health_insurance', 'health_insurance_start'),
        ),
        segment(
            'h3:Bank Information',
            'bank_info',
            'iban',
            css='secondary'
        ),
        'address',
        'curriculum_vitae',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # some tweaks before migrating the model
        self.has_health_insurance.label = "Has insurance plan?"
        self.bank_info.label = ""
        self.iddoc.label = "ID Document"
        self.nif.label = "NIF"

    def __has_permissions(self):
        """Custom method to check authorizations since PyForms ModelForm
        only inherits the permissions system for inlines.
        Once this is fixed, the following methods should be cleaned up.
        """
        user = PyFormsMiddleware.user()
        return any([
            user.is_superuser,
            settings.PROFILE_HUMAN_RESOURCES in user.groups.all(),
        ])

    def has_view_permissions(self):
        return self.__has_permissions() or super().has_view_permissions()

    def has_update_permissions(self):
        return self.__has_permissions() or super().has_update_permissions()
