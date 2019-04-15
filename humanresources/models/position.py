from django.db import models


class Position(models.Model):
    """
    Represents the position a person has in the institute
    Example: Principal Invertigator, Research Technician, PhD Student
    """

    name = models.CharField(max_length=200)

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains", )

    class Meta:
        app_label = 'humanresources'
        ordering = ['name', ]

    def __str__(self):
        return self.name
