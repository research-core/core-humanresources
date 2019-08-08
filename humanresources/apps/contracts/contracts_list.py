from django.conf import settings

from confapp import conf
from pyforms.controls import ControlCheckBox
from pyforms_web.widgets.django import ModelAdminWidget

from humanresources.models import Contract

from .contracts_form import ContractEditFormWidget
from .contracts_create import ContractCreateFormWidget

from django.contrib.contenttypes.models import ContentType
from permissions.models         import Permission


class ContractsListWidget(ModelAdminWidget):
    """
    """
    UID = 'contracts'
    TITLE = 'Contracts'

    MODEL = Contract

    LIST_DISPLAY = [
        'person',
        'ref',
        'position',
        'start',
        'end',
        'is_active'
    ]

    SEARCH_FIELDS = [
        'person__full_name__icontains',
        'ref__icontains'
    ]

    LIST_FILTER = [
         # FIXME AttributeError: 'ManyToOneRel' object has no attribute 'get_limit_choices_to'
         'payout__project',
    ]

    LIST_ROWS_PER_PAGE = 15

    EDITFORM_CLASS = ContractEditFormWidget
    ADDFORM_CLASS = ContractCreateFormWidget

    # Orquestra Configuration
    # =========================================================================

    LAYOUT_POSITION = conf.ORQUESTRA_HOME_FULL

    USE_DETAILS_TO_EDIT = False

    ORQUESTRA_MENU = 'middle-left>HRDashboard'
    ORQUESTRA_MENU_ICON = 'file'
    ORQUESTRA_MENU_ORDER = 3

    """
    @classmethod
    def has_permissions(cls, user):
        if user.is_superuser:
            return True

        return get_ranked_permissions_queryset(
            user, cls.MODEL, ['app_access_contracts']).exists()
    """

    def __init__(self, *args, **kwargs):

        self._active_filter = ControlCheckBox(
            'Only active',
            default=True,
            label_visible=False,
            changed_event=self.populate_list
        )

        self._expiring_filter = ControlCheckBox(
            'Expiring',
            default=False,
            label_visible=False,
            changed_event=self.populate_list
        )

        self._expiringpayouts_filter = ControlCheckBox(
            'Expiring payouts',
            default=False,
            label_visible=False,
            changed_event=self.populate_list
        )

        self._noproposals_filter = ControlCheckBox(
            'No active proposals',
            default=False,
            label_visible=False,
            changed_event=self.populate_list
        )

        super().__init__(*args, **kwargs)

        if hasattr(self, '_add_btn'):
            self._add_btn.field_css = 'ten wide'

    def get_toolbar_buttons(self, has_add_permission=False):
        return tuple(
            (['_add_btn'] if has_add_permission else []) + [
                '_active_filter',
                '_expiring_filter',
                '_expiringpayouts_filter',
                '_noproposals_filter',
            ]
        )

    def get_queryset(self, request, qs):

        if self._expiring_filter.value:
            qs = qs.expiring_soon()

        if self._active_filter.value:
            qs = qs.active()

        if self._expiringpayouts_filter.value:
            qs = qs.expiring_payouts()

        if self._noproposals_filter.value:
            qs = qs.no_active_proposals()

        return qs
