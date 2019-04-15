from PIL import Image
from sorl.thumbnail import delete

from confapp import conf

from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth.models import Group as AuthGroup

from pyforms_web.widgets.django import ModelAdminWidget
from pyforms_web.widgets.django import ModelFormWidget
from pyforms.basewidget import segment
from pyforms.basewidget import no_columns
from pyforms.controls import ControlImg
from pyforms.controls import ControlButton

from common.models import InstitutionAffiliation
from humanresources.models import AcademicCareer
from humanresources.models import Person
from research.models import GroupMember
from .privateinfo import PrivateInfoFormWidget
from ..proposals import ContractProposalsListWidget
from ..contracts import ContractsListWidget


class AcademicCareerInline(ModelAdminWidget):
    MODEL = AcademicCareer

    LIST_DISPLAY = ['institution', 'degree', 'field_of_study', 'graduation_year']

    FIELDSETS = [
        ('institution', 'degree', 'field_of_study', 'graduation_year')
    ]


class InstitutionAffiliationInline(ModelAdminWidget):
    MODEL = InstitutionAffiliation
    TITLE = 'Affiliation'

    LIST_DISPLAY = ['institution', 'date_joined', 'date_left']

    FIELDSETS = [
        ('institution', 'date_joined', 'date_left')
    ]


class ResearchGroupsInline(ModelAdminWidget):
    MODEL = GroupMember
    TITLE = 'Research Groups'

    LIST_DISPLAY = ['group', 'position', 'date_joined', 'date_left', 'membercategory']

    FIELDSETS = [
        ('group', 'position', 'date_joined', 'date_left', 'membercategory')
    ]


class UserAuthGroupsForm(ModelFormWidget):
    """Minimalistic User form only able to modify User groups."""
    MODEL = AuthUser
    FIELDSETS = ['groups']

    def __init__(self, *args, **kwargs):
        """
        Since we are coming from AuthGroup model, we need to
        redirect the PKs before showing the form.
        """
        person = Person.objects.get(pk=kwargs['parent_pk'])
        user   = person.djangouser
        kwargs['pk']    = user.pk
        kwargs['model'] = self.MODEL

        super().__init__(*args, **kwargs)


class AuthGroupsInline(ModelAdminWidget):
    MODEL = AuthGroup
    TITLE = 'Django Authorization Groups'

    EDITFORM_CLASS = UserAuthGroupsForm

    LIST_DISPLAY = ['name']

    AUTHORIZED_GROUPS = ['superuser', settings.APP_PROFILE_HR_PEOPLE]

    def get_queryset(self, request, queryset):
        person = Person.objects.get(pk=self.parent_pk)
        user = person.djangouser
        return user.groups.all()

    def has_add_permissions(self):
        # should always be False, use the Django Admin to manage these groups
        return False

    def has_remove_permissions(self, obj):
        # should always be False, use the Django Admin to manage these groups
        return False









class PeopleFormWidget(ModelFormWidget):
    """
    The advanced version of the form should only be available to
    administrators.
    """
    LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB

    HAS_CANCEL_BTN_ON_EDIT = False
    CLOSE_ON_REMOVE        = True

    FIELDSETS = [
        no_columns('_privateinfo_btn', '_proposals_btn', '_contracts_btn', 'person_active'),
        'h3:PERSONAL INFORMATION',
        (
            segment(
                'full_name',
                ('person_first', 'person_last'),
                ('person_gender', 'person_birthday'),
                ('degree', 'position'),
                ('person_cv', ' '),
                'person_bio',
                field_css='fourteen wide',
            ),
            segment(
                '_img',
                '_rotimg_btn',
                'person_img',
                field_style='max-width:330px;'
            )
        ),
        'h3:EDUCATION',
        segment('AcademicCareerInline'),
        'h3:CONTACT INFORMATION',
        segment(
            ('person_email', 'person_personalemail'),
            ('person_mobile', 'person_phoneext'),
            'person_emergencycontact',
            css='secondary'
        ),
        'h3:INSTITUTIONAL INFORMATION',
        segment(
            'InstitutionAffiliationInline',
            ('person_cardnum', 'person_room'),
            'djangouser',
            css='secondary'
        ),
        'h3:GROUPS',
        segment('ResearchGroupsInline', css='blue'),
        'h3:AUTH GROUPS',
        segment('AuthGroupsInline', css='red')
    ]

    READ_ONLY = ['djangouser']

    INLINES = [
        AcademicCareerInline,
        InstitutionAffiliationInline,
        ResearchGroupsInline,
        AuthGroupsInline,
    ]

    AUTHORIZED_GROUPS = ['superuser']


    @classmethod
    def has_permissions(cls, user):
        from .person_list import PeopleListWidget
        return PeopleListWidget.has_permissions(user)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, 'person_active'):
            self.person_active.label_visible = False
            self.person_active.field_style = 'text-align: right;margin-top:5px;'
            self.person_active.field_css = 'two wide'

        self._privateinfo_btn = ControlButton(
            '<i class="icon lock" ></i>Private info',
            default=self.__privateinfo_btn_evt,
            label_visible=False,
            css='basic red'
        )
        self._contracts_btn = ControlButton(
            '<i class="icon file alternate" ></i>Contracts',
            default=self.__contracts_btn_evt,
            label_visible=False,
            css='basic'
        )
        self._proposals_btn = ControlButton(
            '<i class="icon file alternate outline" ></i>Proposals',
            default=self.__proposals_btn_evt,
            label_visible=False,
            css='basic'
        )
        self._rotimg_btn = ControlButton(
            '<i class="icon undo" ></i>Rotate',
            default=self.__rotimg_evt,
            label_visible=False,
            style='margin-top:5px;',
            field_style='text-align: right;',
            css='mini')

        self._img = ControlImg('Image', label_visible=False)

        self.person_img.changed_event = self.__update_image_evt

        if self.model_object is None:
            self._contracts_btn.hide()
            self._proposals_btn.hide()
            self._privateinfo_btn.hide()
        else:
            self.__update_image_evt()

    def __update_image_evt(self):
        url = self.model_object.thumbnail_url(geometry_string='300x300')
        self._img.value = url + '?t=' + str(timezone.now().timestamp())

    def __rotimg_evt(self):
        delete(self.person_img.filepath, delete_file=False)
        im = Image.open(self.person_img.filepath)
        rot = im.rotate(90)
        rot.save(self.person_img.filepath)
        self.__update_image_evt()

    def __privateinfo_btn_evt(self):
        obj = self.model_object
        if obj:
            privateinfo = obj.get_privateinfo()
            app = PrivateInfoFormWidget(
                pk=privateinfo.pk,
                title=str(privateinfo),
                has_cancel_btn=False,
            )
            app.LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB

    def __proposals_btn_evt(self):
        obj = self.model_object
        if not obj:
            return

        app = ContractProposalsListWidget(
            parent_pk=obj.pk,
            parent_model=Person,
            has_cancel_btn=False,
        )
        app.LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB

    def __contracts_btn_evt(self):
        obj = self.model_object
        if not obj:
            return

        app = ContractsListWidget(
            parent_pk=obj.pk,
            parent_model=Person,
            has_cancel_btn=False,
        )
        app.LAYOUT_POSITION = conf.ORQUESTRA_NEW_TAB

    @property
    def title(self):
        obj = self.model_object
        if obj is None:
            return ModelFormWidget.title.fget(self)
        else:
            return "Person: {0}".format(obj.name)

    @title.setter
    def title(self, value):
        ModelFormWidget.title.fset(self, value)