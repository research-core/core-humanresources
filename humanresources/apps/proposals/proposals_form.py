

from django.urls import reverse

from confapp import conf
from pyforms.basewidget import segment, no_columns
from pyforms.controls import ControlButton
from pyforms.controls import ControlImg
from pyforms_web.web.middleware import PyFormsMiddleware
from pyforms_web.widgets.django import ModelAdminWidget
from pyforms_web.widgets.django import ModelFormWidget

from humanresources.models import ContractProposal
from humanresources.models import Payment
from people.models import Person

from .proposals_create import CreateContractProposalFormWidget
from humanresources.apps.contracts.contracts_form import ContractEditFormWidget


class PaymentEditInline(ModelFormWidget):
    MODEL = Payment
    TITLE = 'Payments'

    FIELDSETS = [
        'project',
        ('n_months', 'amount')
    ]

    def autocomplete_search(self, queryset, keyword, control):
        if control == self.project:
            return queryset.active()
        return queryset


class PaymentInline(ModelAdminWidget):
    """
    Permissions should be given to anyone able to edit the
    corresponding ContractProposal.
    """

    MODEL = Payment
    TITLE = 'Payments'

    LIST_DISPLAY = ['amount', 'project', 'n_months']

    EDITFORM_CLASS = PaymentEditInline

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





class EditContractProposalFormWidget(CreateContractProposalFormWidget):

    MODEL = ContractProposal

    TITLE = 'Edit contract proposal'

    LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB
    HAS_CANCEL_BTN_ON_EDIT = False
    CLOSE_ON_REMOVE = True

    READ_ONLY = (
        'motive',
        'end_date',
        'responsible',
        'closingdate',
        'created_on',
        'closed_by',
        'status_changed',
    )

    FIELDSETS = [
        no_columns('_print', '_goto_contract', style='float:right'),
        segment(
            (
                'motive',
                'created_on',
                'responsible',
                'status',
                'status_changed'
            ),
            css='green'
        ),
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
        ),
        segment('PaymentInline')
    ]

    INLINES = [PaymentInline]


    @classmethod
    def has_permissions(cls, user):
        from .proposals_list import ContractProposalsListWidget
        return ContractProposalsListWidget.has_permissions(user)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        url = reverse('print-proposal', args=[kwargs.get('pk')])

        self._print = ControlButton(
            '<i class="ui icon print"></i>Print',
            default='window.open("{0}", "_blank");'.format(url),
            css='basic blue',
            label_visible=False,
        )

        self._goto_contract = ControlButton(
            '<i class="ui icon file"></i>Go to Contract',
            default=self.__goto_contract_evt,
            css='basic green',
            label_visible=False,
        )

        self._img = ControlImg('Image', label_visible=False)

        # check if the user has print permissions
        if not self.has_print_permissions:
            self._print.hide()

        self.person.changed_event = self.__update_image_evt

        proposal_status = self.model_object.status
        if proposal_status not in ('approved',):
            self._goto_contract.hide()

        self.__update_image_evt()

    @property
    def has_print_permissions(self):
        if not hasattr(self, '_has_print_permissions'):
            user = PyFormsMiddleware.user()
            self._has_print_permissions = ContractProposal.objects.filter(pk=self.object_pk).has_print_permissions(user)
        return self._has_print_permissions

    @property
    def has_approve_permissions(self):
        if not hasattr(self, '_has_approve_permissions'):
            user = PyFormsMiddleware.user()
            self._has_approve_permissions = ContractProposal.objects.filter(pk=self.object_pk).has_approve_permissions(user)
        return self._has_approve_permissions

    def get_readonly(self, default):
        if not (self.has_print_permissions or self.has_approve_permissions):
            default = tuple(list(default) + ['status'])
        return default

    def save_event(self, obj, new_object):

        if self.status.value == 'approved' and not self.model_object.person:
            self.alert('Select a Person from the list to approve this Proposal')
        elif self.status.value == 'approved' and not self.model_object.contract:
            self.tmp_popup_data = dict(obj=obj, new_object=new_object)
            self.message_popup(
                msg="Approving this proposal will generate a contract and lock future modification.\nAre you sure you want to continue?",
                title="Proposal Approval",
                buttons=('Proceed',),
                handler=self.__approve_proposal_evt,
                msg_type='info',
            )
            return None
        elif self.model_object.contract:
            self.alert('A Contract associated with this Proposal already exists .')
        else:
            return super().save_event(obj, new_object)

    def __update_image_evt(self):
        try:
            person = Person.objects.get(pk=self.person.value)
        except Person.DoesNotExist:
            url = Person.DEFAULT_PICTURE_URL
        else:
            url = person.thumbnail_url('300x300')
        self._img.value = url

    def __goto_contract_evt(self):
        if not self.model_object.contract:
            self.alert(
                'Contract does not exist yet. Save the approved'
                ' Proposal to generate the Contract.'
            )
            return
        app = ContractEditFormWidget(
            pk=self.model_object.contract.pk,
            title='Contract: {0}'.format(self.model_object.person.name),
        )
        app.LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB

    def __approve_proposal_evt(self, popup, button):
        if button == 'Proceed':
            user = PyFormsMiddleware.user()
            obj, new_object = self.tmp_popup_data.values()

            proposals = ContractProposal.objects.filter(pk=obj.pk)

            if proposals.has_approve_permissions(user):
                super().save_event(obj, new_object)
                self.model_object.generate_contract(user=user)
                popup.close()
                self.success("Contract created successfully.")
                self._goto_contract.show()
            else:
                popup.alert('You do not have permissions to approve the proposals.')

    @property
    def title(self):
        obj = self.model_object
        if obj is None:
            return ModelFormWidget.title.fget(self)
        else:
            return "Proposal: {0}".format(obj)

    @title.setter
    def title(self, value):
        ModelFormWidget.title.fset(self, value)


class EditProposal(EditContractProposalFormWidget):

    def __init__(self, proposal_id):
        super().__init__(pk=proposal_id)
