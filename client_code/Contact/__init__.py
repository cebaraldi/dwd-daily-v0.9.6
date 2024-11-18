from ._anvil_designer import ContactTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

class Contact(ContactTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
  
    def bt_submit_click(self, **event_args):
        name = self.tb_name.text
        email = self.tb_email.text
        feedback = self.ta_feeback
#        #if anvil.server.call('validate_email', email):
#        #anvil.server.call('send_feedback', name, email, feedback)
        anvil.server.call('send_feedback', 'cebaraldi@gmail.com', name, email, feedback)
        self.bt_submit.enabled = False
        self.tb_name.text = ''
        self.ta_feeback.text = ''
        self.tb_email.text = ''

    def ta_feeback_change(self, **event_args):
        self.bt_submit.enabled = True


