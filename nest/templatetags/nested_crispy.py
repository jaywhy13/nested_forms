from django.template import Node, NodeList
from django import template
from django.utils.safestring import mark_safe

from crispy_forms.helper import FormHelper
from crispy_forms.templatetags.crispy_forms_tags import CrispyFormNode

register = template.Library()


class HtmlContent(Node):

    def __init__(self, html):
        self.html = html

    def render(self, context):
        return mark_safe(self.html)

class KnockoutFormTemplate(Node):
    """ This template node is responsible for rendering <script> templates
        for all children form of a given form.
        TODO: Ensure templates are not rendered twice.
    """

    def __init__(self, form):
        self.form_var = template.Variable(form)

    def render(self, context):
        nodelist = NodeList()
        form = self.form_var.resolve(context)
        child_forms = []
        # recursively find all inline_form that need to get printed
        while hasattr(form, "child_form"):
            child_forms.append((form.child_form, form))
            form = form.child_form

        if not child_forms:
            print("%s has no inline forms" % type(form))

        # Loop through each and get the knockout templates for each
        for child_form, parent_form in child_forms:
            child_form = child_form() if isinstance(child_form, type) else child_form
            # Add knockoutjs bindings to the child form fields
            prefix = parent_form.inline_form.prefix
            for field_name, field in child_form.fields.iteritems():
                field.widget.attrs["data-bind"] = mark_safe("attr: { id: 'id_%s' + '-' + index + '-%s', name: '%s-' + index + '-%s'}" % (prefix, field_name, prefix, field_name))
            form_name = child_form.__class__.__name__
            template_name = "%s-template" % form_name
            context["child_%s" % form_name] = child_form
            nodelist.append(HtmlContent('<script type="text/html" id="%s">' % template_name))
            nodelist.append(CrispyFormNode(form="child_%s" % form_name, helper=None))
            nodelist.append(HtmlContent("</script>"))
        return nodelist.render(context)

class NestedFormNodeJs(Node):
    """ This is node for printing out the JS code to activate knockout for the 
        management form.
    """
    def __init__(self, form):
        self.form = form
        self.form_var = template.Variable(form)

    def render(self, context):
        actual_form = self.form_var.resolve(context)
        child_template_name = "%s-template" % actual_form.child_form.__name__
        form_name = actual_form.get_form_name()

        num_forms = len(actual_form.inline_form.forms)

        nodelist = NodeList()
        form_div_class = "%s_form_div" % form_name

        # Add the script to activate this form
        nodelist.append(HtmlContent("""
            <script> 
                $(document).ready(function(){
                    ko.applyBindings(new ManagementForm('%s', '%s', %s), jQuery(".%s").get()[0]);
                });
            </script>
            """ % (form_name, child_template_name, num_forms, form_div_class)))
        nodelist.append(HtmlContent("</div>"))

        return nodelist.render(context)


class NestedFormNode(Node):
    """ This is the node for the `nested_form` tag. This is responsible for
        printing out the parent form, any children form, management form (hidden)
    """

    def __init__(self, form, helper):
        self.form = form
        self.helper = helper
        self.form_var = template.Variable(form)
        self.helper_var = template.Variable(helper) if helper else None

    def render(self, context):
        actual_form = self.form_var.resolve(context)
        form_name = actual_form.get_form_name()
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
        management_form = actual_form.inline_form.management_form


        """ Basically we create a node list and all the following things to it:
            - <div class='FormName_form_div'> - HtmlContent
                - The actual form (parent)
                -  The management form (hidden)
                - <div class='FormName_children_div'></div>
                - Inline actions form (if one exists)
                - Knockout form templates
            - </div>
            Then we return nodelist.render
        """

        # Add the forms to the nodelist
        nodelist = NodeList()
        # Add the main form to our node list

        # Create a DIV to store the entire form
        form_div_class = "%s_form_div" % form_name
        nodelist.append(HtmlContent("<div class='%s'>" % form_div_class))
        nodelist.append(CrispyFormNode(form=self.form, helper=self.helper))

        # Stuff some other stuff in the context for resolving later
        context["inline_form"] = actual_form.inline_form
        #context["inline_form_management"] = management_form
        context["management_form_helper"] = management_form_helper

        # The inline form HAS the management form... 
        # The inline form prints out the child rows 
        # It ALSO prints out the management form
        nodelist.append(CrispyFormNode(form="inline_form", helper=self.helper))

        # Place a data binding on the management form for KnockoutJS
        fields = management_form.fields
        fields["TOTAL_FORMS"].widget.attrs["data-bind"] = "value: totalForms"
        fields["INITIAL_FORMS"].widget.attrs["data-bind"] = "value: initialForms"
        fields["MAX_NUM_FORMS"].widget.attrs["data-bind"] = "value: maxForms"

        # Check if there is an inline form
        if hasattr(actual_form, "inline_actions_form") and \
                actual_form.inline_actions_form is not None:
            context["inline_actions_form"] = actual_form.inline_actions_form
            nodelist.append(CrispyFormNode(form="inline_actions_form", helper=self.helper))

        nodelist.append(KnockoutFormTemplate(self.form))

        # Add a DIV for the children
        children_div_class = "%s_children_div" % form_name
        nodelist.append(HtmlContent("<div class='%s'>" % children_div_class))
        # Current KIDS should be printed here BTW
        nodelist.append(HtmlContent("</div>"))

        nodelist.append(HtmlContent("</div>"))
        return nodelist.render(context)

@register.tag
def nested_form(parser, token):
    tokens = token.split_contents()
    form = tokens.pop(1) # pop the 2nd item, skip the tag name
    try:
        helper = tokens.pop(1)
    except IndexError:
        helper = None
    return NestedFormNode(form, helper)

@register.tag
def nested_form_js(parser, token):
    tokens = token.split_contents()
    form = tokens.pop(1)
    return NestedFormNodeJs(form)
