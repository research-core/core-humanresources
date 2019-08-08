from django.db import models
from django.db.models import Q

from permissions.models import Permission


class PrivateInfoQuerySet(models.QuerySet):

    # User dependent Querysets
    # =========================================================================

    def owned_by(self, user):
        """
        Filters the Queryset to objects owned by the User or where
        he is referenced in a Foreign Key.

        This is by default what everyone sees if they have no permissions.
        """
        return self.filter( Q(person__auth_user=user) ).distinct()

    def managed_by(self, user, required_codenames):
        """
        Filters the Queryset to objects the user is allowed to manage
        given his Authorization Group profiles.

        Uses the RankedPermissions table.
        """
        ranked_permissions = Permission.objects.filter_by_auth_permissions(
            user, self.model, required_codenames)

        if ranked_permissions.exists():
            # check if the user has permissions to all people
            if ranked_permissions.filter(researchgroup=None).exists():
                return self
            else:

                # check which groups the user has to its people
                groups_withaccess = [p.researchgroup for p in ranked_permissions]
                rankings = [(p.researchgroup, p.ranking) for p in ranked_permissions]

                qs = self.filter(person__group__in=groups_withaccess)

                or_filter = Q()
                for researchgroup, ranking in rankings:
                    or_filter.add(
                        Q(person__auth_user__groups__rankedpermissions__researchgroup=researchgroup) &
                        Q(person__auth_user__groups__rankedpermissions__ranking__gte=ranking), Q.OR
                    )
                return qs.exclude(~Q(person__auth_user=user) & or_filter).distinct()

        # By default returns only the Person associated to the user
        return self.owned_by(user).distinct()

    # PyForms Querysets
    # =========================================================================

    def list_permissions(self, user):
        return self.managed_by(user, ['view', 'change'])

    def has_add_permissions(self, user):
        return Permission.objects.filter_by_auth_permissions(
            user=user,
            model=self.model,
            codenames=['add'],
        ).exists()

    def has_view_permissions(self, user):
        # view_permission is useless because we let people see
        # their own objects via list_permissions
        return self.list_permissions(user).exists()

    def has_update_permissions(self, user):
        return self.managed_by(user, ['change']).exists()

    def has_remove_permissions(self, user):
        return self.managed_by(user, ['delete']).exists()
