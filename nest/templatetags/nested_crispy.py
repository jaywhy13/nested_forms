from django.template import Node, NodeList
from django import template
from crispy_forms.helper import FormHelper
from crispy_forms.templatetags.crispy_forms_tags import CrispyFormNode

register = template.Library()

class CompositeNode(Node):

    def __init__(self, form, helper):
        self.form = form
        self.helper = helper
        self.form_var = template.Variable(form)
        self.helper_var = template.Variable(helper) if helper else None

    def render(self, context):
        actual_form = self.form_var.resolve(context)
        if self.helper is not None:
            actual_helper = self.helper_var.resolve(context)
        else:
            actual_helper = FormHelper() if not hasattr(actual_form, 'helper') \
                else actual_form.helper

        if actual_helper.form_tag:
            raise template.TemplateSyntaxError("form_tag cannot be True on the helper, please go and rectify that")

        management_form_helper = FormHelper()
        management_form_helper.form_tag = False
        management_form_helper.disable_csrf = True


        # Add the forms to the nodelist
        nodelist = NodeList()
        # Add the main form to our node list
        nodelist.append(CrispyFormNode(form=self.form, helper=self.helper))

        # Stuff some other stuff in the context for resolving later
        context["inline_form"] = actual_form.inline_form
        context["inline_form_management"] = actual_form.inline_form.management_form
        context["management_form_helper"] = management_form_helper
        # Seems we don't need the inline form bcuz the management form prints it out...
        #nodelist.append(CrispyFormNode(form="inline_form", helper=self.helper))
        nodelist.append(CrispyFormNode(form="inline_form_management", helper="management_form_helper"))
        # Check if there is an inline form
        if hasattr(actual_form, "inline_actions_form") and \
                actual_form.inline_actions_form is not None:
            context["inline_actions_form"] = actual_form.inline_actions_form
            nodelist.append(CrispyFormNode(form="inline_actions_form", helper=self.helper))
        return nodelist.render(context)

@register.tag
def nested_form(parser, token):
    tokens = token.split_contents()
    form = tokens.pop(1) # pop the 2nd item, skip the tag name
    try:
        helper = tokens.pop(1)
    except IndexError:
        helper = None
    return CompositeNode(form, helper)
