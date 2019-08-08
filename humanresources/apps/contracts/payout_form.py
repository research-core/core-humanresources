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
        ('start', 'end', 'amount', 'total'),
        ('order', '_reqnumber', '_reqdate', '_reqvalue'),
        '_order_btn'
    ]

    def __init__(self, *args, **kwargs):
        super(PayoutEditForm, self).__init__(*args, **kwargs)

        self._reqnumber = ControlInteger('Requision number')
        self._reqdate = ControlDate('Requision date')
        self._order_btn = ControlButton(
            'Order', default=self.__order_btn_evt, label_visible=False, css='basic')
        self._reqvalue = ControlText('Requisition value', readonly=True)

        self.order.hide()
        self._reqnumber.hide()
        self._reqdate.hide()
        # self._currency.hide()
        self._reqvalue.hide()

        if self.model_object:
            order = self.model_object.order
            if order is not None:
                self._reqnumber.value = order.requisition_number
                self._reqdate.value = order.requisition_date
                self._reqvalue.value = order.amount
                # try:
                #self._currency.value = order.currency.pk
                # except:
                #     self._currency.value = None
                self.order.show()
                self._reqnumber.show()
                self._reqdate.show()
                # self._currency.show()
                self._reqvalue.show()

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

        if obj and obj.order:
            obj.order.requisition_number = self._reqnumber.value
            obj.order.requisition_date = self._reqdate.value
            obj.order.currency = Currency.objects.get(currency_name=settings.DEFAULT_CURRENCY_NAME)
            obj.order.save()
            self.order.value = str(obj.order)
            self._reqvalue.value = str(obj.order.order_amount)

        self.total.value = obj.total
        return res

    def autocomplete_search(self, queryset, keyword, control):
        if control == self.financeproject:
            return queryset.active()
        return queryset
