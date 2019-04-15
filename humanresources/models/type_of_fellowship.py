from django.db import models


class TypeOfFellowship(models.Model):
    typeoffellowship_id = models.AutoField(primary_key=True)
    typeoffellowship_name = models.CharField('Name',max_length=100)

    def __str__(self): return self.typeoffellowship_name

    class Meta:
        verbose_name = "Type of fellowship"
        verbose_name_plural = "Types of fellowships"
        # abstract = True
        app_label = 'humanresources'