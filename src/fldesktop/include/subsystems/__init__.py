from fldesktop.include.subsystems import (
    fs3, ui, configmgr, os_manager, pkgmgr
)


subsystems = {
    "ui": ui,
    "fs3": fs3,
    "cfgmgr": configmgr,
    "osmgr": os_manager,
    "pkgmgr": pkgmgr
}


init_seq = [
    "extsvinit",
    "osmgr",

    "ui",
    "ui.desktop",
    "ui.superfx",
    "ui.thememgr",
    "ui.fadeeffect",
    "ui.startupscreen",

    "fs3",
    "pkgmgr",
    "cfgmgr",
    "ui.appserver",

    "ui.localemgr",
    "ui.inputmgr",
    "ui.iconmgr",
    "ui.appletmgr",
    "ui.search",
    "ui.panel",
    "ui.uikit",
    "ui.background",
    "ui.wm",
    "ui.systemsounds",
    "ui.lockscreen"
]


cleanup_seq = list(init_seq)
cleanup_seq.reverse()
