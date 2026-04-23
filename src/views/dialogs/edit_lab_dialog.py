import logging
from datetime import date
from tkinter import messagebox

from models import Lab
from services.labs import update_lab
from views.dialogs.add_lab_dialog import AddLabDialog

log = logging.getLogger(__name__)


class EditLabDialog(AddLabDialog):
    """Modal dialog for editing an existing lab draw.

    Reuses AddLabDialog's layout and validation. Pre-populates fields from
    the given Lab and routes save through services.labs.update_lab so an
    audit row is written.
    """

    def __init__(self, parent, conn, lab: Lab, on_save=None):
        self._editing_lab = lab
        super().__init__(parent, conn, lab.patient_id, on_save=on_save)
        self.title("Edit Lab Values")
        self._populate_from_lab()

    def _populate_from_lab(self):
        lab = self._editing_lab
        lab_date = lab.lab_date
        if hasattr(lab_date, 'isoformat'):
            self.date_var.set(lab_date.isoformat())
        else:
            self.date_var.set(str(lab_date))
        self.anc_var.set('' if lab.anc is None else str(lab.anc))
        self.wbc_var.set('' if lab.wbc is None else str(lab.wbc))
        self.platelets_var.set('' if lab.platelets is None else str(lab.platelets))
        self.hgb_var.set('' if lab.hemoglobin is None else str(lab.hemoglobin))
        self._initial = {
            'date':      self.date_var.get(),
            'anc':       self.anc_var.get(),
            'wbc':       self.wbc_var.get(),
            'platelets': self.platelets_var.get(),
            'hgb':       self.hgb_var.get(),
        }

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            return
        self.error_label.config(text="")

        warnings = self._get_warnings()
        if warnings:
            msg = '\n'.join(f'• {w}' for w in warnings) + '\n\nSave anyway?'
            if not messagebox.askyesno('Unusual Values', msg, parent=self):
                return

        data = self.get_form_data()
        try:
            updated = Lab(
                id=self._editing_lab.id,
                patient_id=self._editing_lab.patient_id,
                lab_date=date.fromisoformat(data['lab_date']),
                anc=float(data['anc']),
                wbc=self._parse_optional(data['wbc']),
                platelets=self._parse_optional(data['platelets']),
                hemoglobin=self._parse_optional(data['hgb']),
            )
            update_lab(self.conn, updated)
        except Exception as e:
            log.exception('Failed to update lab id=%s', self._editing_lab.id)
            messagebox.showerror('Save Failed', f'Could not save lab data:\n{e}',
                                 parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()
