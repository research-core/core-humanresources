from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Q

from common.models import Permissions
from django.contrib.contenttypes.models import ContentType


class PersonQuerySet(models.QuerySet):

    def filter_by_groups(self, groups):
        return self.filter(group__in=groups)

    def active(self):
        """
        Filter only active people
        """
        return self.filter(person_active=True)

    def noactivecontract(self):
        """
        Filter all the people without active contracts
        """
        today = timezone.now().date()

        qs = self.extra(where=["""
            NOT EXISTS (SELECT 1 FROM humanresources_contract b WHERE b.person_id = humanresources_person.person_id and b.contract_start<='{0}' and b.contract_end>='{0}')
        """.format(today.strftime('%Y-%m-%d'))
        ])
        return qs

    def noactiveproposal(self):
        """
        Filter all the people without active proposals
        """
        today = timezone.now().date()

        qs = self.extra(where=["""
            NOT EXISTS (SELECT 1 FROM humanresources_contractproposal c WHERE c.person_id = humanresources_person.person_id and
            c.contractproposal_start<='{0}' and
            DATE_ADD(DATE_ADD(c.contractproposal_start, INTERVAL c.contractproposal_duration_additional_days DAY), INTERVAL c.contractproposal_duration MONTH)>='{0}')
        """.format(today.strftime('%Y-%m-%d'))
        ])
        return qs

    def nostartdate(self):
        """
        Filter all people without start date
        """
        return self.filter(person_datejoined=None)

    def noenddate(self):
        """
        Filter all people without end date
        """
        return self.filter(person_end=None)

    # PyForms Querysets
    # =========================================================================

    def __query_permissions(self, user, permissions_filter):
        # Search for the user groups with certain permissions
        contenttype = ContentType.objects.get_for_model(self.model)
        authgroups  = user.groups.filter(permissions__content_type=contenttype)
        authgroups  = authgroups.filter(permissions_filter).distinct()
        return Permissions.objects.filter(djangogroup__in=authgroups)

    def __filter_by_permissions(self, user, perms):
        if user.is_superuser: return self

        if perms.exists():
            # check if the user has permissions to all people
            if perms.filter(researchgroup=None).exists():
                return self
            else:
                if perms.exists():
                    # check which research groups the user has to its people
                    groups_withaccess = [p.researchgroup for p in perms]
                    rankings = [(p.researchgroup, p.ranking) for p in perms]


                    rankfilters = Q()
                    for researchgroup, ranking in rankings:
                        rankfilters.add(Q(researchgroup=researchgroup, ranking__gte=ranking), Q.OR)
                    rankperms = Permissions.objects.filter(rankfilters)

                    qs = self.exclude(
                        ~Q(djangouser=user) &
                        Q(djangouser__groups__rankedpermissions__in=rankperms)
                    )

                    now = timezone.now()
                    qs = qs.filter(
                        Q(djangouser=user) |
                        Q(
                            groupmember__date_joined__lte=now,
                            groupmember__date_left__gte=now,
                            groupmember__group__in=groups_withaccess
                        ) |
                        Q(
                            groupmember__date_joined__lte=now,
                            groupmember__date_left__isnull=True,
                            groupmember__group__in=groups_withaccess
                        ) |
                        Q(
                            groupmember__date_joined__isnull=True,
                            groupmember__date_left__isnull=True,
                            groupmember__group__in=groups_withaccess
                        )
                    )
                    return qs.distinct()

        # By default returns only the Person associated to the user
        return self.filter(djangouser=user).distinct()

    def list_permissions(self, user):
        # If super user then return all the People
        if user.is_superuser: return self

        # Search for the user groups with certain permissions
        perms = self.__query_permissions(user, Q(permissions__codename='view_person') | Q(permissions__codename='change_person'))
        return self.__filter_by_permissions(user, perms)


    def has_add_permissions(self, user):
        return self.__query_permissions(
            user,
            Q(permissions__codename='add_person')
        ).exists()

    def has_view_permissions(self, user):
        perms = self.__query_permissions( user, Q(permissions__codename='view_person') | Q(permissions__codename='change_person') )
        return self.__filter_by_permissions(user, perms).exists()

    def has_update_permissions(self, user):
        perms = self.__query_permissions( user,  Q(permissions__codename='change_person') )
        return self.__filter_by_permissions(user, perms).exists()

    def has_remove_permissions(self, user):
        perms = self.__query_permissions( user, Q(permissions__codename='delete_person') )
        return self.__filter_by_permissions(user, perms).exclude(djangouser=user).exists()
