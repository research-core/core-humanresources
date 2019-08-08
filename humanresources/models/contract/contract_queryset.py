from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.contrib.auth.models import User

from people.models import Person
from permissions.models         import Permission
from humanresources.models import ContractProposal

class ContractQuerySet(models.QuerySet):

    def active(self):
        now = timezone.now()
        return self.filter(start__lte=now, end__gte=now)

    def no_active_proposals(self):
        proposals = ContractProposal.objects.active()
        people = proposals.values('person')
        return self.exclude(~Q(person__in=people))

    def expiring_soon(self):
        now = timezone.now()
        limit_date = now + relativedelta(days=settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE )
        return self.filter(end__range=[now, limit_date])

    def expired(self):
        now = timezone.now()
        return self.filter(end__lt=now)

    def expiring_payouts(self):
        now = timezone.now()
        limit_date = now + relativedelta(days=settings.ENDING_CONTRACT_WARNING_N_DAYS_BEFORE)

        # exclude all the contracts with payouts with ending at the end of the contract
        qs = self.exclude(payout__end__gte=F('end'))

        # filter all the contracts with payouts ending before the limit date
        qs = qs.filter(payout__end__lte=limit_date)
        return qs.distinct()

    # User dependent Querysets
    # =========================================================================

    def owned_by(self, user):
        """
        Filters the Queryset to objects owned by the User or where
        he is referenced in a Foreign Key.

        This is by default what everyone sees if they have no permissions.
        """
        return self.filter(
            Q(person__auth_user=user)
            |
            Q(supervisor__auth_user=user)
        ).distinct()

    def managed_by(self, user, required_codenames, default=None):
        """
        Filters the Queryset to objects the user is allowed to manage
        given his Authorization Group profiles.

        Uses the RankedPermissions table.
        """

        if default is None:
            default = self.none()

        if user.is_superuser: return self

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

                rankfilters = Q()
                for researchgroup, ranking in rankings:
                    rankfilters.add(Q(researchgroup=researchgroup, ranking__gte=ranking), Q.OR)
                rankperms = Permission.objects.filter(rankfilters)

                persons = Person.objects.filter(group__in=groups_withaccess)
                persons = persons.exclude(
                    ~Q(auth_user=user) &
                    Q(auth_user__groups__rankedpermissions__in=rankperms)
                ).distinct()


                filters = Q()

                # Show the contracts from the user
                filters.add(Q(person__auth_user=user), Q.OR)

                # Show the contracts the user is supervisor
                filters.add(Q(supervisor__auth_user=user), Q.OR)

                # Show the people from groups with visibility
                filters.add(Q(
                    person__groupmember__date_joined__lte=F('start'),
                    person__groupmember__date_left__gte=F('end'),
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

                return self.filter(filters).distinct()

        return default.distinct()

    # PyForms Querysets
    # =========================================================================

    def list_permissions(self, user):
        return self.managed_by(
            user,
            ['view', 'change'],
            default=self.owned_by(user)
        )

    def has_add_permissions(self, user):
        return Permission.objects.filter_by_auth_permissions(
            user=user,
            model=self.model,
            codenames=['add'],
        ).exists()

    def has_view_permissions(self, user):
        # view_permission is useless because we let people see
        # their own objects via list_permissions
        return self.list_permissions(user)

    def has_update_permissions(self, user):
        res = self.managed_by(user, ['change'])

        return False if res is None else res.exists()

    def has_remove_permissions(self, user):
        res = self.managed_by(user, ['delete'])

        return False if res is None else res.exists()
