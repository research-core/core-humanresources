from django.conf import settings

from pyforms.basewidget import BaseWidget
from confapp import conf

from .dashboards import ExpiringContracts


class HumanResourcesOverviewWidget(BaseWidget):
    """
    """
    UID = 'humanresources'
    TITLE = 'human resources'.title()

    # Orquestra Configuration
    # =========================================================================

    # LAYOUT_POSITION = conf.ORQUESTRA_HOME

    ORQUESTRA_MENU = 'left'
    ORQUESTRA_MENU_ICON = 'users'
    ORQUESTRA_MENU_ORDER = 10

    AUTHORIZED_GROUPS = ['superuser', settings.APP_PROFILE_HR_PEOPLE]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #ExpiringContracts()
