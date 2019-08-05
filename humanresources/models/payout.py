import datetime
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.utils.html import format_html
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group as AuthGroup

from suppliers.models import Supplier
from finance.models import ExpenseCode
from orders.models import Order
from orders.models import OrderExpenseCode
from common.models import Currency


class Payout(models.Model):
    """
    Represents a payout in a contract.
    """

    payout_id     = models.AutoField(primary_key=True)  #: ID
    payout_start  = models.DateField('Start date', blank=True, null=True)
    payout_end    = models.DateField('End date', blank=True, null=True)
    payout_amount = models.DecimalField('Monthly amount', blank=False, null=False, max_digits=15, decimal_places=2)#: FinanceProject.amount=sum(FinanceProjects.Payout)

    #hidden column, to be updated automaticly
    total  = models.DecimalField('Total amount', max_digits=15, decimal_places=2, blank=True, default=0)

    order = models.ForeignKey('orders.Order', verbose_name='Order', blank=True, null=True, on_delete=models.CASCADE)  #: Fk to the order of this payout
    contract = models.ForeignKey('Contract', verbose_name='Contract', on_delete=models.CASCADE)  #: Fk to the Contract of this payout
    financeproject = models.ForeignKey(
        'finance.Project',
        verbose_name='Finance Project',
        limit_choices_to={'expensecode__expensecode_number': '01'},
        on_delete=models.CASCADE,
    )  #: Fk to the Finance Project of this payout

    class Meta:
        ordering = ['payout_start', ]
        verbose_name = "payout"
        verbose_name_plural = "payouts"
        app_label = 'humanresources'

    def __str__(self):
        return str(self.payout_amount)

    def reqNum(self):
        try:
            if self.order.order_reqnum!=None and self.order.order_reqnum!=None:
                return format_html("<a href='/finance/order/{0}/'>{1}</a>".format(self.order.pk, self.order.order_reqnum))
            else:
                return format_html("<a href='/finance/order/{0}/'>Missing requisition number</a>".format(self.order.pk))
        except:
            return "No order"
    reqNum.short_description = 'Requisition number'
    reqNum.allow_tags = True


    def delete(self):
        if self.order: self.order.delete()
        return super(Payout, self).delete()

    def totalAmount(self):
        if self.payout_end==None: return "Set the payout end"
        payout_end = self.payout_end + datetime.timedelta(1)
        diff = relativedelta( payout_end, self.payout_start)
        amount = self.payout_amount
        if amount==None: amount = 0.0
        return round(float(diff.years)*12*float(amount)+float(diff.months)*float(amount)+float(diff.days)*(float(amount)/30), 2)
    totalAmount.short_description = 'Total amount'

    def update_order(self, user):
        """
        Because for every Payout a requisition is made, we automatically
        generate the associated Order using this method. This Order
        object is pre filled with default information and has the
        Requisition Number field blank for future update.
        """
        # no finance project is associated
        if self.financeproject is None:

            # remove the existing order
            if self.order is not None:
                self.order.orderexpensecode_set.all().delete()
                self.order.delete()
                self.order = None

        elif self.order is None:
            supplier, created = Supplier.objects.get_or_create(
                supplier_name="General Human Resources")

            expensecode = ExpenseCode.objects.get(
                expensecode_number="01",
                financeproject=self.financeproject,
            )
            neworder = Order(
                order_amount=self.totalAmount(),
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
            self.order.order_amount = self.totalAmount()
            self.order.save()

            expcode = OrderExpenseCode.objects.get(
                order=self.order,
            )
            expcode.orderexpensecode_amount = self.totalAmount()
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

        self.total = self.totalAmount() 
        super(Payout, self).save(*args, **kwargs)
