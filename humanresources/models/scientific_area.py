from django.db import models


class ScientificArea(models.Model):
    """
    Represents the Scientific Area of a person
    Example: Neuroscience, Medicine
    """
    
    scientificarea_id = models.AutoField(primary_key=True)          #: ID
    scientificarea_name = models.CharField('Name', max_length=100)  #: Name

    class Meta:
        ordering = ['scientificarea_name',]
        verbose_name = "Scientific area"
        verbose_name_plural = "People - Scientific areas"
        # abstract = True
        app_label = 'humanresources'

    def __str__(self):
        return self.scientificarea_name

    @staticmethod
    def autocomplete_search_fields():
        return ("scientificarea_name__icontains", )
