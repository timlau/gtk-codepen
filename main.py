#  Copyright (C) 2021 Tim Lauridsen < tla[at]rasmil.dk >
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to
#  the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

"""
CSS Codepen like application for GTK
"""
import sys
import os
import os.path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, Gdk, GLib, GtkSource, Gio  # type: ignore


class App(Gtk.Application):
    __gtype_name__ = 'GtkMyApp'
    windows_title = "Gtk3 CSS Codepen"
    default_css = './user.css'

    def __init__(self):
        Gtk.Application.__init__(self, application_id="dk.rasmil.sourceview")
        self.connect("activate", self.on_activate)
        self.builder = Gtk.Builder()
        self.builder.add_from_file('main.ui')
        self.demo_ui = Gtk.Builder()
        self.demo_ui.add_from_file('demo.ui')
        self.current_css_file = self.default_css

    def on_activate(self, app):
        self.window = self.builder.get_object('mainwin')
        self.window.set_application(app)
        self.window.set_title(self.windows_title)
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
        # setup buttons
        for id_name in ['apply_css', 'open', 'save']:
            btn = self.builder.get_object(id_name)
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
        buffer.set_highlight_matching_brackets(False)
        lang_manager = GtkSource.LanguageManager()
        buffer.set_language(lang_manager.get_language('css'))
        style_mgr = GtkSource.StyleSchemeManager()
        # print(f' Styles: {style_mgr.props.scheme_ids}')
        style = style_mgr.get_scheme('solarized-light')
        buffer.set_style_scheme(style)
        return buffer, sourceview

    def load_file(self, filename=None):
        if not filename:
            filename = 'demo.css'
        print(f'Loading : {filename}')
        file = GtkSource.File()
        file.set_location(Gio.File.new_for_path(filename))
        loader = GtkSource.FileLoader.new(self.buffer, file)
        loader.load_async(GLib.PRIORITY_LOW, None, None, None, None, None)

    def save_file(self, filename):
        print(f'Saving : {filename}')
        file = GtkSource.File()
        file.set_location(Gio.File.new_for_path(filename))
        loader = GtkSource.FileSaver.new(self.buffer, file)
        loader.save_async(GLib.PRIORITY_LOW, None, None, None, None, None)

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

    def file_open(self):
        dialog = Gtk.FileChooserDialog(
            action=Gtk.FileChooserAction.OPEN, title="Select a .CSS file")
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                   Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.add_buttons(*buttons)
        flt = Gtk.FileFilter()
        flt.set_name("Content Style Sheet files")
        flt.add_pattern("*.css")
        dialog.add_filter(flt)
        dialog.set_current_folder('.')
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            self.load_file(file_path)
            self.current_css_file = file_path
            self.window.set_title(
                f'{self.windows_title} - {os.path.basename(file_path)}')
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def file_save(self, overwrite=False):
        dialog = Gtk.FileChooserDialog(
            action=Gtk.FileChooserAction.SAVE, title="Save File")
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                   Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dialog.add_buttons(*buttons)
        flt = Gtk.FileFilter()
        flt.set_name("Content Style Sheet files")
        flt.add_pattern("*.css")
        dialog.add_filter(flt)
        dialog.set_current_folder(os.path.dirname(self.current_css_file))
        dialog.set_filename(self.current_css_file)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            if not os.path.exists(file_path) or overwrite or self.save_overwrite(file_path):
                self.save_file(file_path)
                self.current_css_file = file_path
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def save_overwrite(self, file_path):
        messagedialog = Gtk.MessageDialog(transient_for=self.window,
                                          modal=True,
                                          destroy_with_parent=True,
                                          message_type=Gtk.MessageType.INFO,
                                          buttons=Gtk.ButtonsType.YES_NO,
                                          text=f"Do you want to overwrite ? {os.path.basename(file_path)}")
        messagedialog.set_default_response(Gtk.ResponseType.NO)
        response = messagedialog.run()
        messagedialog.destroy()
        return response == Gtk.ResponseType.YES

    def on_button_clicked(self, widget):
        label = widget.get_label()
        # print(f'Button {label} Pressed')
        if label == 'gtk-apply':
            txt = self.buffer.get_text(
                self.buffer.get_start_iter(), self.buffer.get_end_iter(), False)
            self.update_css()
        elif label == "gtk-open":
            self.file_open()
        elif label == "gtk-save":
            self.file_save()


if __name__ == '__main__':
    app = App()
    app.run(sys.argv)
