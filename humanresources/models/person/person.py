import warnings
from common.models import Permissions
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from research.models import Group as ResearchGroup

from django.db.models import Q
from humanresources.models.privateinfo.privateinfo import PrivateInfo

from datetime import datetime
from django.utils.html import format_html
from django.utils.text import slugify
from sorl.thumbnail import get_thumbnail
from django.utils    import timezone



from .person_queryset import PersonQuerySet



class Person(models.Model):
    """
    Represents a Person in the system
    Example: Adam Kampff, Ana Elias
    """

    DEFAULT_PICTURE_URL = '/static/square-image.png'

    person_id       = models.AutoField(primary_key=True)  #: ID
    person_first    = models.CharField('First name', max_length=40, help_text='This field will appear in the website.')                            #: First Name
    person_last     = models.CharField('Last name', max_length=40, help_text='This field will appear in the website.')                              #: Last Name
    person_email    = models.EmailField('Research email', help_text='This field will appear in the website.')                  #: Institution Email
    person_personalemail = models.EmailField('Personal email', blank=True, null=True)       #: Personal Email
    person_phoneext = models.IntegerField('Phone extension', blank=True, null=True)         #: Phone Etension
    person_mobile   = models.CharField('Mobile',max_length=20, blank=True, null=True)         #: Mobile Phone Number
    person_bio      = models.TextField('Biography', blank=True, null=True, default='', help_text='This field will appear in the website.')           #: Biography text
    person_birthday = models.DateField('Birthday', blank=True, null=True,)                  #: Birthday Date
    person_img      = models.ImageField(upload_to="uploads/person/person_img", max_length=150, blank=True, verbose_name='Picture', help_text='This field will appear in the website.')  #: Picture link
    person_cv       = models.FileField('Short Vitae', upload_to="uploads/person/person_cv", blank=True, null=True, help_text='This field will appear in the website.')                   #: CV link
    person_room     = models.CharField('Room',max_length=10, blank=True, null=True)     #: Room Number
    person_emergencycontact = models.TextField('Emergency contacts',max_length=100, blank=True, null=True, default='')
    person_gender   = models.CharField('Gender', max_length=1, choices=( ('F','Female'),('M','Male') ) )
    person_active   = models.BooleanField('Active', default=True)
    person_cardnum  = models.IntegerField('Card number', blank=True, null=True)
    #group = models.ForeignKey(Group, blank=False, null=False, verbose_name='Group Lab', related_name = 'Group Lab', on_delete=models.CASCADE) #: Fk The user that closed that proposal
    djangouser = models.ForeignKey(User, blank=True, null=True, verbose_name='User', related_name = 'person_user', on_delete=models.CASCADE)

    degree          = models.ForeignKey('Degree', blank=True, null=True, on_delete=models.PROTECT)                       #: Degree

    full_name = models.CharField('Name', max_length=150)

    position = models.ForeignKey(
        to='Position',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='This field will appear in the website.',
    )

    # Deprecated fields: not used in any frontend
    # Verify no issues arise with cnp-core-sync before removing these
    person_middle   =   models.CharField('Middle name', max_length=100, blank=True)
    person_phone    = models.CharField('Contact',max_length=20, blank=True, null=True, help_text='This field will appear in the website if the next field is checked.')         #: Contact Number
    person_phoneshow = models.BooleanField('Show this contact in the website', default=False)                   #: Check box Show contact in the website
    person_web      = models.URLField('Website', blank=True, null=True, help_text='This field will appear in the website.')     #: URL to the person's website
    person_datejoined = models.DateField('Joined date', blank=True, null=True,)
    person_end      = models.DateField('End date', blank=True, null=True,)
    institution     = models.ForeignKey('Institution', null=True, blank=True, on_delete=models.CASCADE)    #: Institution e.g. CNP, IGC

    objects = PersonQuerySet.as_manager()

    class Meta:
        ordering = ['person_first','person_last' ]
        verbose_name = "Person"
        verbose_name_plural = "People"
        # abstract = True
        app_label = 'humanresources'

        permissions = (
            ("app_access_hr",  "Access [Human Resources] app"),
            ("app_access_people", "Access [People] app"),
        )

    def __str__(self):
        return self.name


    def save(self, *args, **kw):
        """
        the function will create a django user for new person added to
        the data base or for each person that has been changed/saved
        without a django user

        the function will only feed the first name, last name and email
        as feeded in the person data base, and will create auser name
        first name.last name

        the administrator will have to provide a password, permmissions
        and related group in order to give acssess to this user
        """
        if self.djangouser is None:
            if User.objects.filter(email=self.person_email).exists():
                #if there is a user in django with this email
                self.djangouser = User.objects.get(email=self.person_email)
                self.djangouser.is_active=True
                self.djangouser.is_staff=True
                self.djangouser.save()
            else:
                self.djangouser = User.objects.create_user(
                    ".".join(list(map(slugify, [self.person_first, self.person_last]))),
                    self.person_email,
                    last_login=timezone.now()
                )
                self.djangouser.is_active=True
                self.djangouser.is_staff=True
                self.djangouser.first_name  = self.person_first
                self.djangouser.last_name   = self.person_last
                self.djangouser.save()

            from research.models import GroupMember
            memberships = GroupMember.objects.filter(person=self)
            group = Group.objects.get(name=settings.PROFILE_GUEST)
            self.djangouser.groups.add(group)
            for member in memberships:
                if member.group.groupdjango!=None:
                    self.djangouser.groups.add(member.group.groupdjango)
            self.djangouser.save()

            if  self.djangouser.email.endswith('.fchampalimaud.org') and \
                not EmailAddress.objects.filter(email=self.djangouser.email, user=self.djangouser).exists():
                e = EmailAddress(user=self.djangouser, email=self.djangouser.email, verified=True, primary=True)
                e.save()

        # TODO the above code block needs testing and updating
        # TODO create method .join_guest_group() to reuse

        if self.person_active:
            self.djangouser.is_active = True
            # self.djangouser.is_staff = False  # not needed in CORE v2
            # FIXME this needs to be dealt in another way, let everyone be Staff for now
            # TODO join Guest auth group
        else:
            # If Person is set as inactive, revoke all access permissions
            self.djangouser.is_active = False
            self.djangouser.is_staff = False
            self.djangouser.is_superuser = False
            self.djangouser.user_permissions.clear()
            self.djangouser.groups.clear()
        # The active status can be reverted but permissions will require
        # manual assignment
        self.djangouser.save()

        super(Person, self).save(*args, **kw)


    @staticmethod
    def autocomplete_search_fields():
        return ("person_first__icontains", "person_middle__icontains", 'person_last__icontains')

    def fullname(self):
        """To be deprecated in favour of `full_name` field."""
        warnings.warn(
            'Stop using fullname() method, use the full_name field instead',
            DeprecationWarning,
        )
        return self.full_name

    @property
    def name(self):
        return " ".join(filter(None, (self.person_first, self.person_last)))

    def get_privateinfo(self):

        try:
            pinfo = self.privateinfo
        except PrivateInfo.DoesNotExist:
            pinfo = PrivateInfo(person=self)
            pinfo.save()

        return pinfo


    def personprivateinfo(self):
        """
        Return a link "Go" to the "Private info" page where a user with permission
        can read and edit the private information of the selected person.
        If this person still dont have private information, the function
        returns a "Not created yet" label.

        @type  self:    Person
        @rtype:         link
        @return:        link to the "Private info" page of that person
        """
        from humanresources.models import PrivateInfo
        try:
            private = PrivateInfo.objects.get(person=self)
            return format_html("""<a class='btn btn-warning' href='/humanresources/privateinfo/{0}/' ><i class="icon-lock icon-black"></i> Show private info</a>""".format(str(private.privateinfo_id)))
        except ObjectDoesNotExist:
            return format_html("""<a class='btn btn-warning' href='/humanresources/privateinfo/add/?person={0}' ><i class="icon-lock icon-black"></i> Private info</a>""".format(str(self.pk)))

    personprivateinfo.short_description = 'Private info'
    personprivateinfo.allow_tags = True

    def person_contracts(self):
        """
        Return a link "Contracts" to the "Contracts" page where a user with permission
        can read and edit the contracts of the selected person.
        If this person still dont have a contract, the function
        returns a "Not created yet" label.

        @type  self:    Person
        @rtype:         link
        @return:        link to the "contracts" page of that person
        """
        try:
            return format_html("""<a class="btn btn-warning" href='/humanresources/contract/?person_id=%s' ><i class="icon-folder-close icon-black"></i> Show contracts</a>""" % (self.person_id))
        except ObjectDoesNotExist:
            return "Not created yet"
    person_contracts.short_description = 'Contracts'
    person_contracts.allow_tags = True

    def has_active_contract(self):
        """Returns True if at least one of its contracts is active."""
        return self.contract_set.active().exists()

    def get_groups(self):
        """
        Returns a string with the name of all Research Groups this
        Person is a member of.
        """
        return '; '.join([
            membership.group.group_name
            for membership in self.groupmember_set.all()
        ])

    def thumbnail_url(self, geometry_string):
        if self.person_img:
            url = get_thumbnail(
                self.person_img,
                geometry_string,
                crop='center',
                format='PNG',
            ).url
        else:
            url = self.DEFAULT_PICTURE_URL
        return url

    def thumbnail_80x80(self):
        url = self.thumbnail_url(geometry_string='80x80')
        return "<img class='ui top aligned tiny image rounded' src='{url}''>".format(url=url)
    thumbnail_80x80.short_description = ' '

    def photo(self):
        if self.person_img:
            return format_html("""<a class='imageLink' target='_blank'href='%s'><img src='%s' width='50px' height='50px'  ></a>""" % (self.person_img.url,self.person_img.url))
        else:
            return ''
    photo.short_description = 'Picture'
    photo.allow_tags = True





    def personuser(self):

        if self.username:
            return django.contrib.auth.models.User.objects.get(username = self.person_username, is_staff=True, is_active=True,)


    # Object Permissions

    def has_view_permission(self, user):
        if any((
            user.is_superuser,
            user == self.djangouser,
            user.groups.filter(name=settings.PROFILE_HUMAN_RESOURCES).exists(),
        )):
            return True
        else:
            return False

    def has_change_permission(self, user):
        if any((
            user.is_superuser,
            user == self.djangouser,
            user.groups.filter(name=settings.PROFILE_HUMAN_RESOURCES).exists(),
        )):
            return True
        else:
            return False

    ######################################################################################
    #### FILTERS #########################################################################
    ######################################################################################


