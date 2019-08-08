import argparse
from datetime import datetime

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.timezone import now

from dateutil.relativedelta import relativedelta
import csv


def relativedelta_to_str(rd):
    rd_str_parts = []

    if rd.years:
        rd_str_parts.append(f"{rd.years} years")
    if rd.months:
        rd_str_parts.append(f"{rd.months} months")
    if rd.days:
        rd_str_parts.append(f"{rd.days} days")

    return " ".join(rd_str_parts)


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


class Command(BaseCommand):
    help = """

    """

    DEBUG = False
    CSVFILENAME = 'contracts_report.csv'

    def add_arguments(self, parser):
        parser.add_argument('--filter', nargs='+', help='filter people names')
        parser.add_argument(
            '--today',
            help="Count days up to - format YYYY-MM-DD",
            type=valid_date,
        )
        parser.add_argument('--debug', action='store_true', help='debug mode')

    def export_csv(self, data):
        with open(self.CSVFILENAME, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    'name',
                    'position',
                    'salary',
                    'reponsible',
                    'group',
                    'duration',
                    'duration (days)',
                    'notes',
                ]
            )
            for row in data:
                writer.writerow(row)

    def inspect_past_contracts(self, person, first_day, supervisor):
        """Inspect previous contracts for continuity.
        Returns the corrected tuple `(first_day, supervisor)`.
        """

        has_gap = False
        was_student = False
        gap_days = 0

        for contract in person.contract_set.order_by('-start')[1:]:

            if 'student' in contract.position.name.lower():
                was_student = True
                break

            diff = (first_day - contract.end).days
            if diff > 1:
                has_gap = True
                gap_days += diff

            if supervisor is None:
                # update supervisor if missing from recent contracts
                supervisor = contract.supervisor

            if self.DEBUG:
                print(
                    '  |-->  ',
                    contract.ref,
                    contract.start,
                    contract.end,
                    (contract.end - contract.start).days,
                    contract.salary,
                    contract.supervisor,
                )

            first_day = contract.start

        notes = []
        if has_gap:
            notes.append(f"Gap detected ({gap_days} days)")
        if was_student:
            notes.append("Was student")

        return first_day, supervisor, notes

    def handle(self, *args, **options):

        self.DEBUG = options['debug']

        data = []

        Person = apps.get_model('people', 'Person')
        Group = apps.get_model('research', 'Group')

        # get all active people
        active_people = Person.objects.filter(person_active=True)

        # exclude students
        active_people = active_people.exclude(position__name__icontains='student')

        # exclude people without contracts
        people = active_people.exclude(contract=None)

        # apply provided filters
        if options['filter']:
            self.DEBUG = True
            query = Q()
            for s in options['filter']:
                query.add(Q(full_name__icontains=s), Q.OR)
            people = people.filter(query)

        n_expected = people.count()

        today = options['today'] or now().date()

        if self.DEBUG:
            self.stdout.write(
                "Inspecting contract information for %d people" % n_expected
            )

        for person in people.all():

            notes = []

            if self.DEBUG:
                self.stdout.write(
                    "Found %d contracts for %s"
                    % (person.contract_set.count(), person.name)
                )

            last_contract = person.contract_set.order_by('start').last()

            if (
                last_contract.start
                <= today
                <= last_contract.end
            ):
                current_contract = last_contract
            else:
                current_contract = last_contract
                self.stdout.write(
                    self.style.WARNING("%s contract has expired" % person.name)
                )
                notes.append("Using expired contract")

            # duration =

            if self.DEBUG:
                print(
                    '----->  ',
                    current_contract.ref,
                    current_contract.start,
                    current_contract.end,
                    (current_contract.end - current_contract.start).days,
                    current_contract.salary,
                    current_contract.supervisor,
                )

            first_day = current_contract.start
            supervisor = current_contract.supervisor

            first_day, supervisor, extra_notes = self.inspect_past_contracts(
                person, first_day, supervisor
            )

            notes.extend(extra_notes)

            total_duration_days = (today - first_day).days
            total_duration = relativedelta(today, first_day)

            groups = person.group_set.exclude(group_name="Support Units")
            groups_number = groups.count()
            if groups_number > 0:
                if groups_number > 1:
                    groups_names = ', '.join([group.group_name for group in groups])
                    self.stdout.write(
                        self.style.WARNING(
                            "%s belongs to %d groups: %s"
                            % (person.name, groups_number, groups_names)
                        )
                    )
                    notes.append("Multiple groups: %s" % groups_names)
                try:
                    current_group_name = groups.get(
                        group_name="Lab Administration"
                    ).group_name
                except Group.DoesNotExist:
                    current_group_name = groups.first().group_name
            else:
                current_group_name = ""

            # handle special cases here
            # TODO

            if self.DEBUG:
                self.stdout.write(
                    " | ".join(
                        [
                            person.name,
                            str(person.position),
                            f"{current_contract.salary} €",
                            str(supervisor),
                            current_group_name,
                            relativedelta_to_str(total_duration),
                            str(total_duration_days),
                            "; ".join(notes),
                        ]
                    )
                )

            data.append(
                [
                    person.name,
                    person.position,
                    f"{current_contract.salary} €",
                    supervisor,
                    current_group_name,
                    relativedelta_to_str(total_duration),
                    total_duration_days,
                    "; ".join(notes),
                ]
            )

        if n_expected == len(data):
            self.stdout.write(
                self.style.SUCCESS(
                    "Exported contract information for %d people to '%s'"
                    % (n_expected, self.CSVFILENAME)
                )
            )
        else:
            raise ConnectionError("Expected number of people mismatch")

        self.export_csv(data)
