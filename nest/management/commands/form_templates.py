import os
from optparse import make_option
import importlib
import sys

from django.core.management.base import BaseCommand
from django.forms import ModelForm
from django.template import Context
from django.template.loader import get_template
from django.conf import settings

from nest import forms
from nest.forms import NestedModelForm

OUTPUT_DIR = "%s/form_templates" % settings.PROJECT_ROOT
if not os.path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

class Command(BaseCommand):
    help = "This prints out the forms"

    def handle(self, *args, **options):
        # Loop through all installed apps and try to import forms
        modules = []
        forms = []
        for app in settings.INSTALLED_APPS:
            try:
                __import__("%s.forms" % app)
                mod = sys.modules.get("%s.forms" % app)
                modules.append(mod)
            except ImportError:
                pass

        for mod in modules:
            form_list = []
            for form in dir(mod):
                try:
                    """ We are only interested in forms that are a child of 
                        some other form.
                    """ 
                    actual_form = getattr(mod, form)()
                    if isinstance(actual_form, NestedModelForm) and \
                            actual_form.child_form is not None:
                        # Add the class
                        if actual_form.child_form not in form_list:
                            form_list.append(actual_form.child_form)

                except Exception as e:
                    pass

            template = get_template("form_basic.html")
            for child_form in form_list:
                actual_form = child_form()
                form_name = actual_form.get_form_name()
                # disable CSRF on the helper to get rid of the warning
                actual_form.helper.disable_csrf = True
                print("Generating template for: %s" % actual_form.get_form_name())
                html = template.render(Context({"form" : actual_form}))
                filename = "%s/%s.form" % (OUTPUT_DIR, form_name)
                with open(filename, "w") as f:
                    f.write(html)
