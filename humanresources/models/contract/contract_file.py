from django.contrib.auth.models import User
from django.db import models


class ContractFile(models.Model):

    file       = models.FileField(upload_to='contract/contractfile', max_length=255)
    created_on = models.DateField('Created on', auto_now_add=True)
    created_by = models.ForeignKey(User, verbose_name='Created by', on_delete=models.CASCADE)

    contract = models.ForeignKey('Contract', blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_on',]
        verbose_name = "Contract files"
        verbose_name_plural = "Contract file"