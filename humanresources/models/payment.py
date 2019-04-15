from django.db import models
from django.db.models import Q


MONTHS_CHOICES = (
    (1, '1 month'),
    (2, '2 months'),
    (3, '3 months'),
    (4, '4 months'),
    (5, '5 months'),
    (6, '6 months'),
    (7, '7 months'),
    (8, '8 months'),
    (9, '9 months'),
    (10, '10 months'),
    (11, '11 months'),
    (12, '12 months'),
)


class Payment(models.Model):
    """
    Represents a payout information for the contract proposal
    """

    payment_id = models.AutoField(primary_key=True)  #: ID
    payment_amount = models.DecimalField('Monthly amount', blank=False, null=False, max_digits=15, decimal_places=2)#: FinanceProject.amount=sum(FinanceProjects.Payout)
    payment_nmonths = models.IntegerField('Use this finance project for', blank=True, null=True, default=None, choices=MONTHS_CHOICES )

    contractproposal = models.ForeignKey('ContractProposal', verbose_name='Proposal', on_delete=models.CASCADE) #: Fk to the Contract of this payout
    financeproject = models.ForeignKey(
        'finance.FinanceProject',
        verbose_name='Finance Project',
        limit_choices_to={'expensecode__expensecode_number': '01'},
        on_delete=models.CASCADE
    )  #: project of the contract

    class Meta:
        verbose_name = "Proposal payout"
        verbose_name_plural = "Proposal payouts"
        # abstract = True
        app_label = 'humanresources'

    def __str__(self):
        return 'Payout ID: %d' % self.pk

    def payment_numberofmonths(self):
        return dict(MONTHS_CHOICES).get(self.payment_nmonths, '-')
