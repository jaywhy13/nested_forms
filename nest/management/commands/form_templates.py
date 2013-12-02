from django.core.management.base import BaseCommand
from django.forms import ModelForm
from django.template import Context
from django.template.loader import get_template

from nest import forms
from nest.forms import NestedModelForm

class Command(BaseCommand):
    help = "This prints out the forms"

    def handle(self, *args, **options):
        form_list = []
        for form in dir(forms):
            try:            
                actual_form = getattr(forms, form)()
                if isinstance(actual_form, ModelForm):
                    form_list.append(form)
            except Exception:
                pass

        print("Will print templates for: %s" % form_list)
        template = get_template("form_basic.html")
        for form in form_list:
            actual_form = getattr(forms, form)
            html = template.render(Context({"form" : actual_form}))
            print html
            print "\n"