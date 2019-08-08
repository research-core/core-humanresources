from django.db import models


class FellowshipType(models.Model):

    name = models.CharField('Name', max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Fellowship type"
        verbose_name_plural = "Types of fellowships"
