from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings

from django.utils.html import format_html

from localflavor.generic.models import IBANField

from .privateinfo_queryset import PrivateInfoQuerySet


class PrivateInfo(models.Model):
    """
    Represents Private Information of a Person
    Example: Salary, Adress
    """

    privateinfo_id = models.AutoField(primary_key=True)             #: ID
    privateinfo_docnumber = models.CharField('Document number', max_length=500, blank=True, null=True,) #: Document uploaded to the private info page
    privateinfo_docexpiration = models.DateField('Expiration date', blank=True, null=True,)
    privateinfo_socialsecuritynum = models.CharField('Social Security Number', max_length=20, blank=True, null=True,)
    privateinfo_address = models.TextField('Address', blank=True, null=True, default='')    #: A Person Adress in the Private Info form
    privateinfo_cv = models.FileField('Curriculum Vitae', upload_to="uploads/privateinfo/privateinfo_cv", blank=True, null=True)       #: A Person CV file uploaded to the private info form
    privateinfo_bankinfo = models.TextField('Bank Info', blank=True, null=True, default='')    #: Bank Information of a Person in the system
    privateinfo_healthinsurance = models.NullBooleanField('Health Insurance')
    privateinfo_healthinsurancestart = models.DateField('Start date', blank=True, null=True,)

    iban = IBANField(
        verbose_name="IBAN", blank=True, include_countries=("PT",)
    )

    nif = models.CharField(
        verbose_name='NIF',
        max_length=9,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{9}$',
                message='Invalid number',
                code='nomatch',
            ),
        ],
    )

    person       = models.OneToOneField('people.Person', verbose_name='Person', on_delete=models.CASCADE)    #: Name
    iddocument   = models.ForeignKey('IDDocument', blank=True, null=True, verbose_name='ID Document', on_delete=models.CASCADE)      #: Document Id in the private info
    citizenship  = models.ForeignKey('common.Citizenship', blank=True, null=True, on_delete=models.CASCADE)    #: Citizenship e.g. American
    birthcity    = models.ForeignKey('common.City', verbose_name='Birth City', blank=True, null=True, on_delete=models.CASCADE)              #: Birth city of a Person in the private info form
    birthcountry = models.ForeignKey('common.Country', verbose_name='Birth Country', blank=True, null=True, on_delete=models.CASCADE)     #: Birth country of a Person in the Private Info form

    objects = PrivateInfoQuerySet.as_manager()

    def personmoreinfo(self):
        """
        Return a link "Go" to the "Private info" page where a permission user
        can read and edit private information of the selected person.
        If this person still dont have private information, the function
        returns a "Not created yet" label.

        @type  self: Person
        @rtype:   link
        @return:  link to the "Private info" page of that person
        """
        try:
            return format_html(
                """
                <a class='btn btn-warning' href='/humanresources/person/{0}/' >
                <i class="icon-user icon-black"></i>
                Profile
                </a>
                """.format(str(self.person.pk))
            )
        except ObjectDoesNotExist:
            return "Not defined yet!!"
    personmoreinfo.short_description = 'More info'
    personmoreinfo.allow_tags = True

    class Meta:
        ordering = ['person', ]
        verbose_name = "Private Info"
        verbose_name_plural = "Private Info"
        app_label = 'humanresources'

    def __str__(self):
        return self.person.name

    @staticmethod
    def get_queryset(request, qs):
        user = request.user

        if user.is_superuser:
            return qs

        if user.groups.filter(name=settings.PROFILE_HUMAN_RESOURCES).exists():
            return qs

        return qs.filter(person__djangouser=user).distinct()
