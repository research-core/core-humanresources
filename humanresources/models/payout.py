import datetime
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.utils.html import format_html
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group as AuthGroup

from finance.models import ExpenseCode
from common.models  import Currency

try:
    from orders.models import Order
    from orders.models import OrderExpenseCode
    orders_module_installed = 'orders' in settings.INSTALLED_APPS
except:
    orders_module_installed = False

try:
    from suppliers.models import Supplier
    suppliers_module_installed = 'suppliers' in settings.INSTALLED_APPS
except:
    suppliers_module_installed = False




class Payout(models.Model):
    """
    Represents a payout in a contract.
    """

    start  = models.DateField('Start date', blank=True, null=True)
    end    = models.DateField('End date', blank=True, null=True)
    amount = models.DecimalField('Monthly amount', blank=False, null=False, max_digits=15, decimal_places=2)
    total  = models.DecimalField('Total amount', max_digits=15, decimal_places=2, blank=True, default=0)
    contract = models.ForeignKey('Contract', verbose_name='Contract', on_delete=models.CASCADE)
    project  = models.ForeignKey(
        'finance.Project',
        verbose_name='Finance Project',
        limit_choices_to={'expensecode__number': '01'},
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['start', ]
        verbose_name = "payout"
        verbose_name_plural = "payouts"

    def __str__(self):
        return str(self.ammount)

    def delete(self):
        if self.order:
            self.order.delete()
        return super(Payout, self).delete()

    def total_amount(self):

        if self.end==None:
            return "Set the payout end"

        payout_end = self.end + datetime.timedelta(1)
        diff = relativedelta(payout_end, self.start)
        amount = self.amount
        if amount==None: amount = 0.0
        return round(float(diff.years)*12*float(amount)+float(diff.months)*float(amount)+float(diff.days)*(float(amount)/30), 2)
    total_amount.short_description = 'Total amount'

    def update_order(self, user):
        """
        Because for every Payout a requisition is made, we automatically
        generate the associated Order using this method. This Order
        object is pre filled with default information and has the
        Requisition Number field blank for future update.
        """
        if not orders_module_installed:
            return

        # no finance project is associated
        if self.project is None:

            # remove the existing order
            if self.order is not None:
                self.order.orderexpensecode_set.all().delete()
                self.order.delete()
                self.order = None

        elif self.order is None:

            supplier, created = Supplier.objects.get_or_create(
                supplier_name="Human resources"
            )

            expensecode = ExpenseCode.objects.get(
                expensecode_number="01",
                project=self.project,
            )
            neworder = Order(
                order_amount=self.total_amount(),
                order_req=user.username,
                responsible=user,
                supplier=supplier,
                currency=Currency.objects.get(currency_name=settings.DEFAULT_CURRENCY_NAME),
                order_desc="%s's - contract" % self.contract.person,
                order_reqdate=timezone.now(),
                group=AuthGroup.objects.get(name=settings.PROFILE_HUMAN_RESOURCES),
            )
            neworder.save(expensecode_kwargs=dict(expensecode=expensecode))
            self.order = neworder

        elif self.order.order_reqnum is None:


            # In case the requisition was not placed yet,
            # we can still update the order
            self.order.order_amount = self.total_amount()
            self.order.save()

            expcode = OrderExpenseCode.objects.get(
                order=self.order,
            )
            expcode.orderexpensecode_amount = self.total_amount()
            expcode.save()

        else:
            raise Exception(
                'Sorry you cannot change the Payout, '
                'because the requisition number was already submitted.'
            )

    def save(self, *args, **kwargs):

        user = kwargs.pop('user')
        if user is None:
            raise Exception(
                'A User is required to create the Order associated with '
                'this Payout'
            )
        self.update_order(user)

        self.total = self.total_amount()
        super(Payout, self).save(*args, **kwargs)
