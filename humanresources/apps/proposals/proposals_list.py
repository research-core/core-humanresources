from confapp import conf
from pyforms_web.widgets.django import ModelAdminWidget

from permissions.models import Permission
from humanresources.models import ContractProposal

from .proposals_form import EditContractProposalFormWidget
from .proposals_create import CreateContractProposalFormWidget


class ContractProposalsListWidget(ModelAdminWidget):
    """
    """
    UID = 'proposals'
    TITLE = 'Proposals'

    MODEL = ContractProposal

    LIST_DISPLAY = [
        'person_name',
        'position',
        'start',
        'end_date',
        'supervisor',
        'status_icon',
    ]

    SEARCH_FIELDS = (
        'person__first_name__icontains',
        'person__last_name__icontains',
        'person__full_name__icontains',
        'person_name__icontains',
    )

    LIST_FILTER = [
        'status',
        'responsible',
        'supervisor',
        'created_on',
        'start',
    ]

    LIST_ROWS_PER_PAGE = 15

    EXPORT_CSV = True
    EXPORT_CSV_COLUMNS = [
        col.strip('_icon')
        if col.endswith('_icon') else col
        for col in LIST_DISPLAY
    ]

    EDITFORM_CLASS = EditContractProposalFormWidget
    ADDFORM_CLASS = CreateContractProposalFormWidget

    # Orquestra Configuration
    # =========================================================================

    LAYOUT_POSITION = conf.ORQUESTRA_HOME

    USE_DETAILS_TO_EDIT = False

    ORQUESTRA_MENU = 'middle-left>HRDashboard'
    ORQUESTRA_MENU_ICON = 'file outline'
    ORQUESTRA_MENU_ORDER = 2

    @classmethod
    def has_permissions(cls, user):
        if user.is_superuser:
            return True

        return Permission.objects.filter_by_auth_permissions(
            user=user,
            model=cls.MODEL,
            codenames=['add', 'view', 'change'],
        ).exists()
