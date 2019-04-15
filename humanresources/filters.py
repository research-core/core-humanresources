from django.contrib import admin
from django.db import models
from django.utils import timezone


class ContractStatusFilter(admin.SimpleListFilter):
    title = 'status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.active()

        if self.value() == 'expiring':
            return queryset.expiring_soon()

        if self.value() == 'expired':
            return queryset.expired()


class InputFilter(admin.SimpleListFilter):

    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class NextMonthYearDateFieldListFilter(admin.filters.DateFieldListFilter):
    """
    Filter adapted to look up next month/year.
    """

    def __init__(self, field, *args, **kwargs):
        super().__init__(field, *args, **kwargs)

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField
            today = now.date()

        if today.month == 11:
            next_month_2 = today.replace(year=today.year + 1, month=1, day=1)
        elif today.month == 12:
            next_month_2 = today.replace(year=today.year + 1, month=2, day=1)
        else:
            next_month_2 = today.replace(month=today.month + 2, day=1)

        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)

        next_year = today.replace(year=today.year + 1, month=1, day=1)
        next_year_2 = today.replace(year=today.year + 2, month=1, day=1)

        self.links = (
            ('Any date', {}),
            ('This month', {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(next_month),
            }),
            ('Next month', {
                self.lookup_kwarg_since: str(next_month),
                self.lookup_kwarg_until: str(next_month_2),
            }),
            ('This year', {
                self.lookup_kwarg_since: str(today.replace(month=1, day=1)),
                self.lookup_kwarg_until: str(next_year),
            }),
            ('Next year', {
                self.lookup_kwarg_since: str(next_year),
                self.lookup_kwarg_until: str(next_year_2),
            }),
        )
