from pyforms.basewidget import segment, no_columns
from pyforms_web.widgets.django import ModelFormWidget

from ..people_form import PeopleFormWidget, AcademicCareerInline, InstitutionAffiliationInline


class GroupMembersFormWidget(PeopleFormWidget):

    FIELDSETS = [
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
            ),
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
            css='secondary'
        ),
    ]

    READ_ONLY = ['full_name', 'djangouser', 'person_email', 'person_cardnum']

    INLINES = [
        AcademicCareerInline,
        InstitutionAffiliationInline,
    ]


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def has_permissions(cls, user):
        from .person_list import GroupMembersListWidget
        return GroupMembersListWidget.has_permissions(user)

    @property
    def title(self):
        obj = self.model_object
        if obj is None:
            return ModelFormWidget.title.fget(self)
        else:
            return "Member: {0}".format(obj.name)

    @title.setter
    def title(self, value):
        ModelFormWidget.title.fset(self, value)
