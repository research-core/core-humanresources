from django.conf import settings

from pyforms.controls import ControlButton
from pyforms.controls import ControlDate
from pyforms.controls import ControlInteger
from pyforms.controls import ControlText
from pyforms_web.web.middleware import PyFormsMiddleware
from pyforms_web.widgets.django import ModelFormWidget

from humanresources.models import Payout
from common.models import Currency

from frontend.supplier_apps.apps.orders.orders_form import OrderEditFormWidget


class PayoutEditForm(ModelFormWidget):
    MODEL = Payout
    TITLE = 'Payout'

    READ_ONLY = ['reqNum', 'totalAmount', 'order', 'total']

    FIELDSETS = [
        'financeproject',
        ('payout_start', 'payout_end', 'payout_amount', 'total'),
        ('order', '_reqnumber', '_reqdate', '_reqvalue'),
        '_order_btn'
    ]

    def __init__(self, *args, **kwargs):
        super(PayoutEditForm, self).__init__(*args, **kwargs)

        self._reqnumber = ControlInteger('Requision number')
        self._reqdate = ControlDate('Requision date')
        #self._currency  = ControlAutoComplete('Currency', queryset=Currency.objects.all() )
        self._order_btn = ControlButton(
            'Order', default=self.__order_btn_evt, label_visible=False, css='basic')
        self._reqvalue = ControlText('Requision value', readonly=True)

        self.order.hide()
        self._reqnumber.hide()
        self._reqdate.hide()
        # self._currency.hide()
        self._reqvalue.hide()

        if self.model_object:
            order = self.model_object.order
            if order is not None:
                self._reqnumber.value = order.order_reqnum
                self._reqdate.value = order.order_reqdate
                self._reqvalue.value = order.order_amount
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
        obj = self.model_object
        if obj.order:
            OrderEditFormWidget(pk=obj.order.pk)

    def save_object(self, obj):
        obj = super().save_object(obj, user=PyFormsMiddleware.user())

        return obj

    def save_event(self, obj, new_object):
        res = super().save_event(obj, new_object)

        if obj and obj.order:
            obj.order.order_reqnum = self._reqnumber.value
            obj.order.order_reqdate = self._reqdate.value
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
