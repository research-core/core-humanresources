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

    LIST_DISPLAY = ['file', 'created_on']

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
            ('ref', '_openproposal_btn', 'warn_when_ending'),
            ('person', 'supervisor')
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
        ' ',
        segment('PayoutInline', css='blue'),
        ' ',
        segment('FilesInline', css='blue'),
        ' ',
        segment(
            'description',
            'notes',
            css='secondary'
        ),
    ]

    READ_ONLY = (
        'person',
        'supervisor',
        'start',
        'end',
        'description',
        'salary',
        'position',
        'fellowship_type',
        'fellowship_ref',
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

    # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
    def __open_proposal_evt(self):
        obj = self.model_object

        # The import has to be done here to avoid recursive imports
        # between the contracts and the proposals
        from ..proposals.proposals_form import EditContractProposalFormWidget

        for proposal in obj.contractproposal_set.all():
            app = EditContractProposalFormWidget(
                pk=proposal.pk,
                title=str(proposal),
                has_cancel_btn=False
            )
            app.LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB

    def get_contract_start(self):
        return self.model_object.start

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
