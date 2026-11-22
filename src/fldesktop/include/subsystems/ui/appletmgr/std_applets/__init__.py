from fldesktop.include.subsystems.ui.appletmgr.std_applets import (
    calendar, battery, ime, network, power, volume
)


APPLETS = [
    volume.Volume,
    network.Network,
    calendar.Calendar,
    power.Power
]
