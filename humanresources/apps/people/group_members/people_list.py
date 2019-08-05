from django.contrib.contenttypes.models import ContentType
from permissions.models         import Permission

from humanresources.models import Person

from ..people_list import PeopleListWidget
from .people_form import GroupMembersFormWidget

class GroupMembersListWidget(PeopleListWidget):
    """
    People app for group responsibles.
    """
    UID   = 'people'
    TITLE = 'People'

    LIST_DISPLAY = (
        'thumbnail_80x80',
        'full_name',
        'person_email',
        'position',
    )

    EDITFORM_CLASS = GroupMembersFormWidget


    @classmethod
    def has_permissions(cls, user):
        if user.is_superuser: return True

        # Search for the user groups with certain permissions
        contenttype = ContentType.objects.get_for_model(cls.MODEL)
        authgroups  = user.groups.filter(permissions__content_type=contenttype)
        authgroups  = authgroups.filter(permissions__codename='app_access_people')
        return Permissions.objects.filter(djangogroup__in=authgroups).exists()

    def get_queryset(self, request, qs):
        qs = qs.active()

        if self._nocontract_filter.value:
            qs = qs.noactivecontract()

        if self._noproposal_filter.value:
            qs = qs.noactiveproposal()

        return qs

    def get_toolbar_buttons(self, has_add_permission=False):
        return (
            '_add_btn' if has_add_permission else None,
            '_nocontract_filter',
            '_noproposal_filter',
        )
