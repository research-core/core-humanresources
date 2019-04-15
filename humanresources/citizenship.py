from django.db import models


class Citizenship(models.Model):
    """
    Represents a Person's Citizenship in the system
    Example: American, British
    """
    
    citizenship_id = models.AutoField(primary_key=True)         #: ID
    citizenship_name = models.CharField('Name', max_length=70)  #: Name

    class Meta:
        ordering = ['citizenship_name',]
        verbose_name = "Citizenship"
        verbose_name_plural = "Citizenships"
        app_label = 'common'

    def __str__(self):
        return self.citizenship_name
