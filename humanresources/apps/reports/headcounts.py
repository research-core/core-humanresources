from pyforms.basewidget import BaseWidget
from pyforms.controls import ControlInteger
from pyforms.controls import ControlButton
from pyforms.controls import ControlBarsChart
from pyforms.controls import ControlPieChart
from pyforms.controls import ControlList
from pyforms.controls import ControlDate
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlAutoComplete
from pyforms.controls import ControlQueryList

from django.contrib.auth.models import Group
from django.db.models import Count, Sum
from humanresources.models import Payout
from finance.models import Project, CostCenter

from pyforms_web.organizers import segment, no_columns
from confapp import conf
from django.conf import settings


class HeadcountsReports(BaseWidget):

    UID   = 'headcounts-report'
    TITLE = 'Report'

    LAYOUT_POSITION = conf.ORQUESTRA_HOME_FULL
    ORQUESTRA_MENU = 'middle-left>HRDashboard'
    ORQUESTRA_MENU_ORDER = 20
    ORQUESTRA_MENU_ICON  = 'chart line'

    AUTHORIZED_GROUPS = ['superuser', settings.PROFILE_HUMAN_RESOURCES]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._start     = ControlDate('Start')
        self._end       = ControlDate('End')
        self._groups      = ControlAutoComplete('Groups', multiple=True, queryset=Group.objects.all() )
        self._costcenters = ControlAutoComplete('Cost centers', multiple=True, queryset=CostCenter.objects.all())
        self._projects    = ControlAutoComplete('Projects', multiple=True, queryset=Project.objects.all())
        self._applybtn    = ControlButton('Apply', default=self.populate_report)

        self._updategraphs_btn = ControlButton('Update graphs', default=self.populate_graphs)
        self._projs_pie = ControlPieChart('Projects')
        self._grps_pie  = ControlPieChart('Groups')
        self._fellow_pie = ControlPieChart('Fellowship type')
        self._amount_chart = ControlBarsChart('Amount per date')

        self._list  = ControlQueryList('List', rows_per_page=15, 
            headers=[
                'Person', 'Contract:Start', 'Contract:Until', 'Contract:Salary', 'Contract:Ref',
                'Contract:Position', 'Contract:Fellowship type', 'Contract:Fellowship ref',
                'Paid:Amount', 'Paid:Start', 'Paid:Until', 'Paid:Req. num.', 'Paid:Req. created', 
                'C.C. Group', 'C.C.', 'Proj.', 'Grant'
            ],
            list_display = [
                'contract__person', 'contract__start', 'contract__end', 'contract__salary', 'contract__ref',
                'contract__position', 'contract__fellowship_type', 'contract__fellowship_ref',
                'total', 'start', 'end', 'order__requisition_number', 'order__requisition_date',
                'project__costcenter__group', 'project__costcenter__code', 'project__code',
                'project__grant'
            ] 
        )

        self.formset = [
            no_columns('_start', '_end', '_groups', '_costcenters', '_projects', '_applybtn'),
            segment('_list'),
            (segment('h2:Amount per projects','_projs_pie',css='overflow'), segment('h2:Amount per groups', '_grps_pie', css='overflow') ),
            (segment('h2:Amount per fellowship', '_fellow_pie', css='overflow'), ' '),
            segment('_amount_chart', css='overflow' ),
        ]

    def get_queryset(self):
        start = self._start.value
        end   = self._end.value
    
        qs = Payout.objects.all()

        if start: qs = qs.filter(start__gte=start)
        if end:   qs = qs.filter(end__lte=end)

        if self._groups.value:
            qs = qs.filter(project__costcenter__group__in=self._groups.value)
        
        if self._costcenters.value:
            qs = qs.filter(project__costcenter__in=self._costcenters.value)

        if self._projects.value:
            qs = qs.filter(project__in=self._projects.value)


        #qs.order_by('person', 'contract__contract_start', 'project__costcenter__costcenter_code', 'financeproject__project_code','payout_start')

        return qs

    def populate_report(self):
        qs = self.get_queryset()
        self._list.value = qs

        self.populate_graphs()

    def populate_graphs(self):
        qs = self.get_queryset()
        
        qs0 = qs.values(
            'project__costcenter__code','project__code','project__name'
        ).annotate(total_amount=Sum('total')).order_by('project')
        
        self._projs_pie.value = [( "{0} - {1} - {2}".format(
            row['project__costcenter__code'],
            row['project__code'],
            row['project__name']

        ), row['total_amount']) for row in qs0]


        qs1 = qs.values(
            'project__costcenter__group__name'
        ).annotate(total_amount=Sum('total')).order_by('project__costcenter__group')
        
        self._grps_pie.value = [(row['project__costcenter__group__name'], row['total_amount']) for row in qs1]



        qs2 = qs.values(
            'contract__fellowship_type__name'
        ).annotate(total_amount=Sum('total')).order_by('contract__fellowship_type')
        
        self._fellow_pie.value = [(row['contract__fellowship_type__name'], row['total_amount']) for row in qs2]


        qs3 = qs.values(
            'start__year'
        ).annotate(total_amount=Sum('total')).order_by('start__year')
        
        self._amount_chart.value = {'Amount per date':[(row['start__year'], row['total_amount']) for row in qs3]}

        