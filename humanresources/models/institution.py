from django.db import models


class Institution(models.Model):
    """
    Represents the institution a person belongs to
    Example: CCNP, IGC
    """

    institution_id = models.AutoField(primary_key=True)             #: ID
    institution_name = models.CharField('Name', max_length=200)     #: Name

    class Meta:
        ordering = ['institution_name',]
        verbose_name = "Research Institution"
        verbose_name_plural = "People - Research Institutions"
        # abstract = True
        app_label = 'humanresources'

    def __str__(self):
        return self.institution_name