import hashlib
import os
import time

import gi
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck

CACHE_DIR = (os.getenv('XDG_CACHE_HOME', os.getenv('HOME') + '/.cache')) + '/ulauncher_window_switcher'


def list_windows():
    screen = Wnck.Screen.get_default()
    # We need to force the update as screen is populated lazily by default
    screen.force_update()
    return [window for window in screen.get_windows() if
            # Do not list sticky windows, or the ulauncher prompt
            window.get_workspace() is not None and window.get_application().get_name() != 'ulauncher']


def store_icon_file(icon, name):
    # Some app have crazy names, ensure we use something reasonable
    file_name = hashlib.sha224(name).hexdigest()
    icon_full_path = CACHE_DIR + '/' + file_name + '.png'
    icon.savev(icon_full_path, 'png', [], [])
    return icon_full_path


def activate(window):
    workspace = window.get_workspace()
    # We need to first activate the workspace, otherwise windows on a different workspace might not become visible
    workspace.activate(int(time.time()))
    window.activate(int(time.time()))


def render_window(window):
    window_name = window.get_name()
    app_name = window.get_application().get_name()
    return ExtensionResultItem(icon=store_icon_file(window.get_icon(), app_name),
                               name=app_name,
                               description=window_name,
                               on_enter=ExtensionCustomAction(window.get_xid(), keep_app_open=False))


class WindowSwitcherExtension(Extension):

    def __init__(self):
        super(WindowSwitcherExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        # Ensure the icon cache directory is created
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        return RenderResultListAction([render_window(window) for window in list_windows()])


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        for window in list_windows():
            if window.get_xid() == event.get_data():
                activate(window)


if __name__ == '__main__':
    WindowSwitcherExtension().run()
