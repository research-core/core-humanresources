from django.db import models


class Degree(models.Model):
    """
    Academic degree: MSc, PhD, MD, ...
    """

    degree_id = models.AutoField(primary_key=True)
    degree_name = models.CharField('Degree', max_length=200)
    degree_show = models.NullBooleanField('Show in website')

    # TODO add rank field to help sort by importance

    class Meta:
        ordering = ['degree_name',]
        verbose_name = "Degree"
        verbose_name_plural = "People - Degrees"
        # abstract = True
        app_label = 'humanresources'

    def __str__(self):
        return self.degree_name
