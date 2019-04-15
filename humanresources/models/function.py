from django.db import models


class Function(models.Model):
    """
    DEPRECATED! Use model Position instead.

    This should only be removed when no migrations depend on it.

    ---

    Represents the Function a person has in the institue
    Example: Lab Manager, External student
    """

    function_id = models.AutoField(primary_key=True)                #: ID
    function_name = models.CharField('Function', max_length=200)    #: NameS

    @staticmethod
    def autocomplete_search_fields():
        return ("function_name__icontains", )


    class Meta:
        ordering = ['function_name',]
        verbose_name = "Function"
        verbose_name_plural = "People - Functions"
        # abstract = True
        app_label = 'humanresources'

    def __str__(self):
        return self.function_name
