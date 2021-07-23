
import sys
import gi
import os
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, Gdk, GLib, GtkSource, Gio  # type: ignore


class App(Gtk.Application):
    __gtype_name__ = 'GtkMyApp'

    def __init__(self):
        Gtk.Application.__init__(self, application_id="dk.rasmil.sourceview")
        self.connect("activate", self.on_activate)
        self.builder = Gtk.Builder()
        self.builder.add_from_file('main.ui')
        self.demo_ui = Gtk.Builder()
        self.demo_ui.add_from_file('demo.ui')

    def on_activate(self, app):
        self.window = self.builder.get_object('mainwin')
        self.window.set_application(app)
        self.window.set_title("Gtk3 CSS Codepen")
        self.window.set_default_size(1600, 800)
        self.provider = Gtk.CssProvider()
        # Setup left & right
        self.left = self.builder.get_object('left')
        self.right = self.builder.get_object('right')
        self.right_box = self.demo_ui.get_object('demo_box')
        self.right_box.show_all()
        self.right.add(self.right_box)
        # setup sourceview & buffer
        self.buffer, self.sourceview = self.setup_sourceview()
        # load file into sourceview
        self.load_file()
        btn = self.builder.get_object('apply_css')
        btn.connect('clicked', self.on_button_clicked)
        self.left.add(self.sourceview)
        self.left.show_all()
        self.load_main_css()
        self.apply_css(self.right, self.provider)
        self.window.present()

    def setup_sourceview(self):
        buffer = GtkSource.Buffer()
        sourceview = GtkSource.View.new_with_buffer(buffer)
        sourceview.set_show_line_numbers(True)
        sourceview.set_insert_spaces_instead_of_tabs(True)
        sourceview.set_smart_backspace(True)
        sourceview.set_tab_width(2)
        lang_manager = GtkSource.LanguageManager()
        buffer.set_language(lang_manager.get_language('css'))
        style_mgr = GtkSource.StyleSchemeManager()
        # print(f' Styles: {style_mgr.props.scheme_ids}')
        style = style_mgr.get_scheme('solarized-light')
        buffer.set_style_scheme(style)
        return buffer, sourceview

    def load_file(self):
        file = GtkSource.File()
        file.set_location(Gio.File.new_for_path('demo.css'))
        loader = GtkSource.FileLoader.new(self.buffer, file)
        loader.load_async(GLib.PRIORITY_LOW, None, None, None, None, None)

    def load_main_css(self):
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        try:
            css_provider.load_from_path('main.css')
            context = Gtk.StyleContext()
            context.add_provider_for_screen(screen, css_provider,
                                            Gtk.STYLE_PROVIDER_PRIORITY_USER)
        except GLib.Error as e:
            print(f"Error in theme: {e} ")

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def update_css(self):
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        # self.buffer.remove_all_tags(start, end)
        text = self.buffer.get_text(start, end, False).encode('utf-8')
        try:
            self.provider.load_from_data(text)
        except GLib.GError as e:
            if e.domain != 'gtk-css-provider-error-quark':
                raise e
        Gtk.StyleContext.reset_widgets(Gdk.Screen.get_default())

    def on_button_clicked(self, widget):
        label = widget.get_label()
        # print(f'Button {label} Pressed')
        if label == 'Apply CSS':
            txt = self.buffer.get_text(
                self.buffer.get_start_iter(), self.buffer.get_end_iter(), False)
            self.update_css()


if __name__ == '__main__':
    app = App()
    app.run(sys.argv)
