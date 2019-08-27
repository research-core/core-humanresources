from django.db import models
from django.db.models import Q, F
from django.utils import timezone

from people.models import Person
from permissions.models import Permission
from core_utils.models_functions import MonthsAdd, DaysAdd


class ProposalQuerySet(models.QuerySet):

    def active(self):
        now = timezone.now()
        qs = self
        qs = qs.annotate(proposal_end=DaysAdd(
            MonthsAdd('contractproposal_start', models.F('contractproposal_duration')),
            models.F('contractproposal_duration_additional_days')
        ))
        return qs.filter(
            contractproposal_start__lte=now,
            proposal_end__gte=now
        )

    def owned_by(self, user):
        """
        Filters the Queryset to objects owned by the User or where
        he is referenced in a Foreign Key.

        This is by default what everyone sees if they have no permissions.
        """
        if user.is_superuser:
            return self

        filter = self
        try:
            filter = filter.filter(
                Q(person__auth_user=user) | Q(supervisor__in=user.person) | Q(responsible__user_auth=user)
            )
        except Person.DoesNotExist:
            pass

        return filter.exclude(
            Q(person__auth_user=user) & ~Q(responsible__user_auth=user)
        ).distinct()

    def managed_by(self, user, required_codenames, default=None):
        """
        Filters the Queryset to objects the user is allowed to manage
        given his Authorization Group profiles.

        Uses the RankedPermissions table.
        """

        if default is None:
            default = self.none()

        if user.is_superuser:
            return self

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

                # Find people the user can see ######################################
                rankfilters = Q()
                for researchgroup, ranking in rankings:
                    rankfilters.add(Q(researchgroup=researchgroup, ranking__gte=ranking), Q.OR)
                rankperms = Permission.objects.filter(rankfilters)

                persons = Person.objects.filter(group__in=groups_withaccess)
                persons = persons.exclude(
                    ~Q(auth_user=user) &
                    Q(auth_user__groups__rankedpermissions__in=rankperms)
                ).distinct()
                #####################################################################

                filters = Q()
                # If the proposal is from the user
                filters.add(Q(person__auth_user=user), Q.OR)

                # If the proposal was submitted by the user
                filters.add(Q(responsible__user_auth=user), Q.OR)

                # If the user is the supervisor
                filters.add(Q(supervisor__auth_user=user), Q.OR)

                # Proposal supervisor is of a group managed by user
                filters.add(Q(
                    supervisor__groupmember__group__in=groups_withaccess
                ) & ~Q(
                    supervisor__auth_user__groups__rankedpermissions__in=rankperms
                ), Q.OR)

                # Add the group users
                filters.add(Q(
                    person__groupmember__date_joined__lte=F('start'),
                    person__groupmember__date_left__gte=F('start'),
                    person__groupmember__group__in=groups_withaccess,
                    person__in=persons
                ), Q.OR)
                filters.add(Q(
                    person__groupmember__date_joined__lte=F('start'),
                    person__groupmember__date_left__isnull=True,
                    person__groupmember__group__in=groups_withaccess,
                    person__in=persons
                ), Q.OR)
                filters.add(Q(
                    person__groupmember__date_joined__isnull=True,
                    person__groupmember__date_left__isnull=True,
                    person__groupmember__group__in=groups_withaccess,
                    person__in=persons
                ), Q.OR)

                # Finally, exclude self proposals
                return self.filter(filters).exclude(
                    Q(person__auth_user=user) & ~Q(responsible__user_auth=user)
                ).distinct()

        return default.distinct()

    # PyForms Querysets
    # =========================================================================

    def list_permissions(self, user):
        """Filter objects displayed in List View."""
        return self.managed_by(
            user,
            ['view', 'change'],
            default=self.owned_by(user)
        )

    def has_add_permissions(self, user):
        if user.is_superuser:
            return True

        return Permission.objects.filter_by_auth_permissions(
            user=user,
            model=self.model,
            codenames=['add'],
        ).exists()

    def has_view_permissions(self, user):
        # view_permissions is useless because we let people see
        # their own objects via list_permissions
        return self.list_permissions(user)

    def has_update_permissions(self, user):
        """Can only edit unlocked Proposals"""
        objects = self.managed_by(
            user,
            ['change'],
            default=self.owned_by(user),
        )

        if objects is None:
            return False

        for obj in objects:
            if obj.is_locked():
                return False

        return objects.exists()

    def has_remove_permissions(self, user):
        objects = self.managed_by(
            user,
            ['delete'],
            default=self.owned_by(user)
        )

        if objects is None:
            return False

        for obj in objects:
            if obj.is_locked():
                return False

        return objects.exists()

    def has_print_permissions(self, user):
        return self.managed_by(
            user,
            ['print_proposal'],
        ).exists()

    def has_approve_permissions(self, user):
        return self.managed_by(
            user,
            ['can_approve_contract_proposal'],
        ).exists()
