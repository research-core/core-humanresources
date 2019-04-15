from django.db import models


class FinancingInst(models.Model):
    """
    Represents Financing Institutions
    """
    
    financinginst_id = models.AutoField(primary_key=True)       #: ID
    financinginst_payedby = models.CharField('Paid by', max_length=200, blank=True, null=True,)  #: Payed by information about a Person salary
    financinginst_payment = models.CharField('Payment', blank=True, null=True, max_length=1, choices=( ('B','Bolsa'),('S','Supplement once'),('M','Suplement monthly') ) )
    
    class Meta:
        ordering = ['financinginst_payedby',]
        verbose_name = "Financing Institution"
        verbose_name_plural = "People - Financing Institutions"
        # abstract = True
        app_label = 'humanresources'

    def __str__(self):
        return self.financinginst_payedby