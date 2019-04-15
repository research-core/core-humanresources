from confapp import conf
from pyforms_web.widgets.django import ModelAdminWidget

from common.models import Permissions
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
        'personname',
        'position',
        'contractproposal_start',
        'end_date',
        'supervisor',
        'status_icon',
    ]

    SEARCH_FIELDS = (
        'person__person_first__icontains',
        'person__person_last__icontains',
        'contractproposal_personname__icontains',
    )

    LIST_FILTER = [
        'status',
        'responsible',
        'supervisor',
        'contractproposal_createdon',  # NOT WORKING?
        'contractproposal_start',  # NOT WORKING?
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

    LAYOUT_POSITION = conf.ORQUESTRA_HOME_FULL

    USE_DETAILS_TO_EDIT = False

    ORQUESTRA_MENU = 'left'
    ORQUESTRA_MENU_ICON = 'file outline'
    ORQUESTRA_MENU_ORDER = 2

    @classmethod
    def has_permissions(cls, user):
        if user.is_superuser:
            return True

        return Permissions.objects.filter_by_auth_permissions(
            user=user,
            model=cls.MODEL,
            codenames=['add', 'view', 'change'],
        ).exists()
