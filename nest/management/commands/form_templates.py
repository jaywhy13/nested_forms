import os
from optparse import make_option

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
                import "%s.forms" % app
                mod = sys.modules.get("%s.forms" % app)
                modules.append(mod)
            except ImportError:
                pass

        for mod in modules:
            form_list = []
            for form in dir(mod):
                try:            
                    actual_form = getattr(forms, form)()
                    if isinstance(actual_form, NestedModelForm) and \
                            actual_form.child_form is not None:
                        form_list.append(form)
                except Exception:
                    pass

                print("Will generate templates for: %s" % form_list)
                template = get_template("form_basic.html")
                for form in form_list:
                    actual_form = getattr(forms, form)()
                    form_name = actual_form.get_form_name()
                    # disable CSRF on the helper to get rid of the warning
                    actual_form.helper.disable_csrf = True
                    print("Generating template for: %s" % actual_form.get_form_name())
                    html = template.render(Context({"form" : actual_form}))
                    filename = "%s/%s.form" % (OUTPUT_DIR, form_name)
                    with open(filename, "w") as f:
                        f.write(html)


            

