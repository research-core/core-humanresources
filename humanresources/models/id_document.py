from django.db import models


class IDDocument(models.Model):
    """
    Represents a Document in the system
    Example: CF, CNP
    """

    iddocument_id = models.AutoField(primary_key=True)          #: ID
    iddocument_name = models.CharField('Name', max_length=200)  #: Name

    class Meta:
        ordering = ['iddocument_name',]
        verbose_name = "ID Document type"
        verbose_name_plural = "People - ID Documents types"
        # abstract = True
        app_label = 'humanresources'

    def __str__(self):
        return self.iddocument_name