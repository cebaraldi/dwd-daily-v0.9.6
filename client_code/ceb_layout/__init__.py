from ._anvil_designer import ceb_layoutTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


class ceb_layout(ceb_layoutTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

    def home_link_click(self, **event_args):
        open_form('Home')

    def map_link_click(self, **event_args):
        open_form('Map')

    def about_link_click(self, **event_args):
        open_form('About')

    def contact_link_click(self, **event_args):
        open_form('Contact')
