from pyforms_web.web.middleware import PyFormsMiddleware
from pyforms_web.widgets.django import ModelAdminWidget

from humanresources.models import Payout

from .payout_form import PayoutEditForm


class PayoutInline(ModelAdminWidget):
    MODEL = Payout
    TITLE = 'Payout'

    LIST_DISPLAY = [
        'start',
        'end',
        'amount',
        #'order__requisition_number',
        'project',
    ]

    EDITFORM_CLASS = PayoutEditForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._list.columns_size = ['95px', '95px']

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
