from pyforms.basewidget import BaseWidget
from pyforms.controls import ControlInteger
from pyforms.controls import ControlButton
from pyforms.controls import ControlBarsChart
from pyforms.controls import ControlPieChart
from pyforms.controls import ControlLineChart
from pyforms.controls import ControlList
from pyforms.controls import ControlDate
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlAutoComplete
from pyforms.controls import ControlQueryList
from pyforms.controls import ControlCombo

from people.models  import Person

from confapp import conf
from django.conf import settings
from pyforms_web.organizers import segment, no_columns

from django.db.models       import Count, Sum
from dateutil.rrule import rrule, YEARLY, MONTHLY
from django.utils import timezone
from django.db.models import Q


class PeoplePerYearReport(BaseWidget):

    UID   = 'people-per-year-report'
    TITLE = 'People per year'

    LAYOUT_POSITION = conf.ORQUESTRA_HOME_FULL
    ORQUESTRA_MENU = 'middle-left>HRDashboard'
    ORQUESTRA_MENU_ORDER = 21
    ORQUESTRA_MENU_ICON  = 'chart line'

    AUTHORIZED_GROUPS = ['superuser', settings.PROFILE_HUMAN_RESOURCES]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._start       = ControlDate('Start')
        self._end         = ControlDate('End')
        self._period      = ControlCombo('Period', items=[('Yearly', YEARLY),('Monthly', MONTHLY)], default=YEARLY)
        self._applybtn    = ControlButton('Apply', default=self.populate_graphs)

        self._people_chart  = ControlBarsChart('People per year')
        self._growth0_chart = ControlLineChart('Growth per year')
        
        self._nation_chart  = ControlPieChart('Nationalities')

        self.formset = [
            no_columns('_start', '_end','_applybtn'),
            segment('h2:People','_people_chart', css='overflow'),
            segment('h2:Growth (people)','_growth0_chart', css='overflow'),
            segment('h2:Nationalities','_nation_chart', css='overflow'),
        ]

    def get_queryset(self):
        start = self._start.value
        end   = self._end.value
    
        qs = Person.objects.all()

        if start: qs = qs.exclude(person_end__lte=start)
        if end:   qs = qs.exclude(person_datejoined__gte=end)

        return qs.distinct()

    

    def populate_graphs(self):
        qs = self.get_queryset()

        if not self._start.value:   self._start.value = qs.exclude(person_datejoined=None).order_by(
            'date_joined').first().person_datejoined
        if not self._end.value:     self._end.value   = qs.exclude(person_end=None).order_by('-person_end').first().person_end

        start = self._start.value
        end   = self._end.value

        start = start.replace(day=1, month=1, year=start.year-1)
        end   = end.replace(day=31, month=12)

        people_year = []
        for dt in rrule(YEARLY, dtstart=start, until=end):
            b = dt.replace(day=1, month=1)
            e = dt.replace(day=31, month=12)

            q0 = qs.filter( 
                ( Q(person_datejoined__gte=b) & Q(person_end__lte=e ) ) |
                ( Q(person_datejoined__range=(b,e)) & Q(person_end=None) ) |
                ( Q(person_datejoined__lte=b) & Q(person_end=None) ) |
                ( Q(person_datejoined__lte=b) & Q(person_end__range=(b,e)) ) |
                ( Q(person_datejoined__range=(b,e)) & Q(person_end__gte=e) )
            ).distinct()
            people_year.append( (dt.year, q0.count()) )

        people_movs = []
        for dt in rrule(YEARLY, dtstart=start, until=end):
            b = dt.replace(day=1, month=1)
            e = dt.replace(day=31, month=12)

            q0 = qs.filter( 
                Q(person_datejoined__range=(b,e)) | Q(person_end__range=(b,e) )
            ).distinct()

            people_movs.append( (dt.year, q0.count()) )

        people_joins = []
        for dt in rrule(YEARLY, dtstart=start, until=end):
            b = dt.replace(day=1, month=1)
            e = dt.replace(day=31, month=12)

            q0 = qs.filter( 
                Q(person_datejoined__range=(b,e))
            ).distinct()
            people_joins.append( (dt.year, q0.count()) )

        people_lefts = []
        for dt in rrule(YEARLY, dtstart=start, until=end):
            b = dt.replace(day=1, month=1)
            e = dt.replace(day=31, month=12)

            q0 = qs.filter( 
                Q(person_end__range=(b,e))
            ).distinct()
            people_lefts.append( (dt.year, q0.count()) )



        self._people_chart.value = {
            'People per year':  people_year[1:],
            'Joins and lefts':  people_movs[1:],
            'Joins':            people_joins[1:],
            'Lefts':            people_lefts[1:]
        }


        self._growth0_chart.value = {
            'People per year':  [(n[0],n[1]-n_[1]) for n_, n in zip(people_year, people_year[1:])],
            'Joins and lefts':  [(n[0],n[1]-n_[1]) for n_, n in zip(people_movs, people_movs[1:])],
            'Joins':            [(n[0],n[1]-n_[1]) for n_, n in zip(people_joins, people_joins[1:])],
            'Lefts':            [(n[0],n[1]-n_[1]) for n_, n in zip(people_lefts, people_lefts[1:])]
        }


        qs1 = qs.values('privateinfo__birthcountry__country_name')
        qs1 = qs1.annotate(total=Count('privateinfo__birthcountry__country_name')).order_by('privateinfo__birthcountry__country_name')

        self._nation_chart.value = [
            (
                "{0} ({1})".format(row['privateinfo__birthcountry__country_name'], row['total']), 
                row['total']
            ) for row in qs1
        ]

