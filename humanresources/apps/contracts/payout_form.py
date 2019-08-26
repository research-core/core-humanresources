from django.conf import settings

from pyforms.controls import ControlButton
from pyforms.controls import ControlDate
from pyforms.controls import ControlInteger
from pyforms.controls import ControlText
from pyforms_web.web.middleware import PyFormsMiddleware
from pyforms_web.widgets.django import ModelFormWidget

from humanresources.models import Payout
from common.models import Currency


try:
    from orders.apps.orders.orders_form import OrderEditFormWidget
    orders_module_installed = 'orders' in settings.INSTALLED_APPS
except:
    orders_module_installed = False

class PayoutEditForm(ModelFormWidget):
    MODEL = Payout
    TITLE = 'Payout'

    READ_ONLY = ['requisition_number', 'total_amount', 'order', 'total']

    FIELDSETS = [
        'project',
        ('start', 'end', 'amount', 'total')
    ]

    def __init__(self, *args, **kwargs):
        super(PayoutEditForm, self).__init__(*args, **kwargs)



    def __order_btn_evt(self):
        if not orders_module_installed:
            return

        obj = self.model_object
        if obj.order:
            OrderEditFormWidget(pk=obj.order.pk)

    def save_object(self, obj):
        obj = super().save_object(obj, user=PyFormsMiddleware.user())

        return obj

    def save_event(self, obj, new_object):
        res = super().save_event(obj, new_object)
        self.total.value = obj.total
        return res

    def autocomplete_search(self, queryset, keyword, control):
        if control == self.project:
            return queryset.active()
        return queryset
