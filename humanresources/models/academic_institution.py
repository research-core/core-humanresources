from django.db import models


class AcademicInstitution(models.Model):
    """
    Represents an Academic Institution in the system
    Example: BGU University, Harvard
    """

    academicinstitution_id = models.AutoField(primary_key=True)          # ID
    academicinstitution_name = models.CharField('Name', max_length=200)  # Name

    class Meta:
        ordering = ['academicinstitution_name',]
        verbose_name = "Academic Institution"
        verbose_name_plural = "People - Academic Institutions"
        # abstract = True
        app_label = 'humanresources'

    def __str__(self):
        return self.academicinstitution_name

    @staticmethod
    def autocomplete_search_fields():
        return ("academicinstitution_name__icontains", )
