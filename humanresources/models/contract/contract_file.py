from django.contrib.auth.models import User
from django.db import models


class ContractFile(models.Model):
    contractfile_id = models.AutoField(primary_key=True)
    contractfile_createdon = models.DateField('Created on', auto_now_add=True)
    contractfile_file = models.FileField(upload_to='contract/contractfile', max_length=255)

    createdby = models.ForeignKey(User, verbose_name='Created by', on_delete=models.CASCADE)
    contract = models.ForeignKey('Contract', blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['contractfile_createdon',]
        verbose_name = "Contract files"
        verbose_name_plural = "Contract file"
        # abstract = True
        app_label = 'humanresources'
