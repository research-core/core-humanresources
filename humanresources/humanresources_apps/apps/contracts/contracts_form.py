from confapp import conf

from pyforms.basewidget import segment
from pyforms.controls import ControlButton
from pyforms_web.web.middleware import PyFormsMiddleware
from pyforms_web.widgets.django import ModelAdminWidget
from pyforms_web.widgets.django import ModelFormWidget

from humanresources.models import Contract, ContractFile

from .payout_list import PayoutInline


class FilesFormWidget(ModelFormWidget):
    MODEL = ContractFile
    TITLE = 'Edit contract file'
    FIELDSETS = ['contractfile_file']

    def create_newobject(self):
        obj = super().create_newobject()
        obj.createdby = PyFormsMiddleware.user()
        return obj


class FilesInline(ModelAdminWidget):
    MODEL = ContractFile
    TITLE = 'Contract file'

    LIST_DISPLAY = ['contractfile_file', 'contractfile_createdon']

    EDITFORM_CLASS = FilesFormWidget

    def show_edit_form(self, obj_pk=None):
        obj = self.model.objects.get(pk=obj_pk)

        # Hide object details if user not entitled to update them
        if self.has_update_permissions(obj):
            return super().show_edit_form(obj_pk)
        else:
            return None

    def has_add_permissions(self):
        return self.has_update_permissions(obj=None)

    def has_update_permissions(self, obj):
        user = PyFormsMiddleware.user()
        qs = self.parent_model.objects.filter(pk=self.parent_pk)
        return qs.has_update_permissions(user)

    def has_remove_permissions(self, obj):
        return self.has_update_permissions(obj)


class ContractEditFormWidget(ModelFormWidget):

    TITLE = 'Edit contract'

    MODEL = Contract

    INLINES = [PayoutInline, FilesInline]

    LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB
    HAS_CANCEL_BTN_ON_EDIT = False
    CLOSE_ON_REMOVE = True

    FIELDSETS = [
        'h3:Identification',
        segment(
            ('contract_ref', '_openproposal_btn', 'contract_warningemail'),
            ('person', 'supervisor')
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
        ' ',
        segment('PayoutInline', css='blue'),
        ' ',
        segment('FilesInline', css='blue'),
        ' ',
        segment(
            'contract_scientificdesc',
            'contract_notes',
            css='secondary'
        ),
    ]

    READ_ONLY = (
        'person',
        'supervisor',
        'contract_start',
        'contract_end',
        'contract_scientificdesc',
        'contract_salary',
        'position',
        'typeoffellowship',
        'contract_fellowshipref',
    )

    @classmethod
    def has_permissions(cls, user):
        from .contracts_list import ContractsListWidget
        return ContractsListWidget.has_permissions(user)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._renew_btn = ControlButton(
            '<i class="icon refresh" ></i>Renew',
            default=self.__renew_btn_evt,
            # label_visible=False,
            css='secondary'
        )

        self._openproposal_btn = ControlButton(
            'Proposal', default=self.__open_proposal_evt)

        if self.model_object is None or not self.model_object.can_be_renewed():
            self._renew_btn.hide()

    def __renew_btn_evt(self):
        pass

    def __open_proposal_evt(self):
        obj = self.model_object

        # The import has to be done here to avoid recursive imports
        # between the contracts and the proposals
        from frontend.humanresources_apps.apps.proposals.proposals_form import EditContractProposalFormWidget

        for proposal in obj.contractproposal_set.all():
            app = EditContractProposalFormWidget(
                pk=proposal.pk,
                title=str(proposal),
                has_cancel_btn=False
            )
            app.LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB

    def get_contract_start(self):
        return self.model_object.contract_start

    @property
    def title(self):
        obj = self.model_object
        if obj is None:
            return ModelFormWidget.title.fget(self)
        else:
            return "Contract: {0}".format(obj)

    @title.setter
    def title(self, value):
        ModelFormWidget.title.fset(self, value)
