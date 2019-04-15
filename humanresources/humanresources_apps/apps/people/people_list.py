from confapp import conf
from common.models import Permissions
from humanresources.models import Person
from django.contrib.contenttypes.models import ContentType
from pyforms_web.widgets.django import ModelAdminWidget
from django.conf import settings
from pyforms.controls import ControlCheckBox

from .people_form import PeopleFormWidget

from django.db.models import Q

class PeopleListWidget(ModelAdminWidget):
    """
    """
    UID   = 'hr-people'
    TITLE = 'Human Resources'

    MODEL = Person

    LIST_ROWS_PER_PAGE = 40

    LIST_DISPLAY = (
        'thumbnail_80x80',
        'full_name',
        'person_email',
        'person_active',
    )

    SEARCH_FIELDS = (
        'full_name__icontains',
        'person_email__icontains',
        'person_personalemail__icontains'
    )

    EDITFORM_CLASS = PeopleFormWidget

    EXPORT_CSV = True
    EXPORT_CSV_COLUMNS = [
        # NOTE: These specific columns were asked by Teresa for a report
        'full_name',
        'person_email',
        'has_active_contract',
        'get_groups',
    ]

    # Orquestra Configuration
    # =========================================================================

    LAYOUT_POSITION = conf.ORQUESTRA_HOME_FULL

    USE_DETAILS_TO_EDIT = False

    ORQUESTRA_MENU = 'left'
    ORQUESTRA_MENU_ICON = 'users'
    ORQUESTRA_MENU_ORDER = 1


    @classmethod
    def has_permissions(cls, user):
        if user.is_superuser: return True

        # Search for the user groups with certain permissions
        contenttype = ContentType.objects.get_for_model(cls.MODEL)
        authgroups  = user.groups.filter(permissions__content_type=contenttype)
        authgroups  = authgroups.filter(permissions__codename='app_access_hr')
        perms = Permissions.objects.filter(djangogroup__in=authgroups)
        return perms.exists()

    def __init__(self, *args, **kwargs):

        self._active_filter = ControlCheckBox(
            'Only active',
            default=True,
            label_visible=False,
            changed_event=self.populate_list
        )

        self._nocontract_filter = ControlCheckBox(
            'No contract',
            default=False,
            label_visible=False,
            changed_event=self.populate_list
        )

        self._noproposal_filter = ControlCheckBox(
            'No proposal',
            default=False,
            label_visible=False,
            changed_event=self.populate_list
        )

        super().__init__(*args, **kwargs)

        if hasattr(self, '_add_btn'):
            self._add_btn.field_css = 'fifteen wide'

        self.__check_data_integraty()


    def get_queryset(self, request, qs):

        if self._active_filter.value:
            qs = qs.active()

        if self._nocontract_filter.value:
            qs = qs.noactivecontract()

        if self._noproposal_filter.value:
            qs = qs.noactiveproposal()

        return qs

    def get_toolbar_buttons(self, has_add_permission=False):
        return (
            '_add_btn' if has_add_permission else None,
            '_active_filter',
            '_nocontract_filter',
            '_noproposal_filter',
        )

    def __check_data_integraty(self):
        # FIXME needs update to show useful warnings
        return

        nostartdate = Person.objects.nostartdate()
        if nostartdate.exists():
            self.warning(
                ' <b>|</b> '.join( map(str, nostartdate) ),
                title='People without *joined date* set!')

        noenddate = Person.objects.filter(person_active=False).nostartdate()
        if noenddate.exists():
            self.warning(
                ' <b>|</b> '.join( map(str, noenddate) ),
                title='People without *end date* set!')
