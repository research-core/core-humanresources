from django.db import models


class IDDocument(models.Model):
    """
    Represents a Document in the system
    Example: CF, CNP
    """

    name = models.CharField('Name', max_length=200)  #: Name

    class Meta:
        ordering = ['name',]
        verbose_name = "ID document type"
        verbose_name_plural = "ID documents types"

    def __str__(self):
        return self.name