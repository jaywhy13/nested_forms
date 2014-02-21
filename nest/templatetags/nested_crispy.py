from django.template import Node, NodeList
from django import template
from django.utils.safestring import mark_safe
from django.forms.formsets import BaseFormSet

from crispy_forms.helper import FormHelper
from crispy_forms.templatetags.crispy_forms_tags import CrispyFormNode

from nest.forms import NestedModelForm

register = template.Library()

def get_default_helper():
    helper = FormHelper()
    helper.form_tag = False
    return helper

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
            form = form.child_form()

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
            context["child_%s_helper" % form_name] = get_default_helper()

            nodelist.append(HtmlContent('<script type="text/html" id="%s">' % template_name))
            nodelist.append(CrispyFormNode(form="child_%s" % form_name, 
                helper="child_%s_helper" % form_name))
            if hasattr(child_form, "inline_form"): # then print the management form as well
                """ If our child has a child (e.g. building has tenants)
                    then print the management form for it's child (tenant)
                """
                grand_child_management_form = child_form.inline_form.management_form
                # Tweak it and adds Knockout bindings 
                parent_prefix = parent_form.inline_form.prefix
                child_prefix = child_form.inline_form.prefix
                fields = grand_child_management_form.fields
                for field_name, field in fields.iteritems():
                    field.widget.attrs["data-bind"] = mark_safe("attr: { id: 'id_%s-' + index + '-%s-%s', name: '%s-' + index + '-%s-%s' }" % (parent_prefix, child_prefix, field_name, parent_prefix, child_prefix, field_name))
                context["child_%s_management_form" % form_name] = grand_child_management_form
                context["child_%s_management_form_helper" % form_name] = get_default_helper()
                nodelist.append(CrispyFormNode("child_%s_management_form" % form_name, 
                    "child_%s_management_form_helper" % form_name))
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
        form_name = actual_form.__class__.__name__

        num_forms = len(actual_form.inline_form.forms)

        nodelist = NodeList()
        form_div_class = "%s_form_div" % form_name

        # Add the script to activate this form
        nodelist.append(HtmlContent("""
            <script> 
                $(document).ready(function(){
                    // new ManagementForm(parentForm, childTemplate, initialForms);
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

    def __init__(self, form, helper, top_level=True):
        self.top_level = top_level
        self.form = form
        self.helper = helper
        self.form_var = template.Variable(form)
        self.helper_var = template.Variable(helper) if helper else None

    def render(self, context):
        """ This class has to be able to deal with two classes essentially...
            NestedModelForm and BaseFormset.
            Key thing to note here is that when we get a BaseFormset, 
            what is happening is that the form associated with that 
            BaseFormset has children.
        """
        top_level = self.top_level
        actual_form = self.form_var.resolve(context)
        is_formset = issubclass(actual_form.__class__, BaseFormSet)
        form_name = actual_form.__class__.__name__ if not is_formset \
            else actual_form.form.__name__
        print("Rendering %s (%s) " % (form_name, is_formset))
        if self.helper is not None:
            actual_helper = self.helper_var.resolve(context)
        else:
            actual_helper = FormHelper() if not hasattr(actual_form, 'helper') \
                else actual_form.helper

        if actual_helper.form_tag:
            actual_helper.form_tag = False
            #raise template.TemplateSyntaxError("form_tag cannot be True on the helper, please go and rectify that")

        """ Basically we create a node list and all the following things to it:
            - <div class='FormName_form_div'> - HtmlContent
                - The actual form (parent)
                -  The inline form which prints the children and management form (hidden) 
                - <div class='FormName_children_div'></div>
                - Inline actions form (if one exists)
                - Knockout form templates
            - </div>
            Then we return nodelist.render
        """

        # Add the forms to the nodelist
        nodelist = NodeList()
        # Add the main form to our node list

        # === PRINT THE PARENT FORM
        form_div_class = "%s_form_div" % form_name
        nodelist.append(HtmlContent("<div class='%s'>" % form_div_class))
        if not is_formset:
            nodelist.append(CrispyFormNode(form=self.form, helper=self.helper))
        else:
            print("Prefix: %s, Default prefix: %s" % (actual_form.prefix, actual_form.get_default_prefix()))

        # === PRINT THE KIDS
        if is_formset: # e.g. BuildingFormSet
            # We need to add each form AND print the management form
            for child_index in range(len(actual_form.forms)):
                child_form = actual_form.forms[child_index]
                child_form_name = "%s_%s" % (child_form.__class__.__name__, child_index)
                print(" Adding %s to the nodelist" % child_form_name)
                child_form_helper_name = "%s_helper" % child_form_name
                context[child_form_name] = child_form
                context[child_form_helper_name] = child_form.helper if hasattr(child_form, "helper") else None
                if hasattr(child_form, "inline_form"):
                    print(" %s is a NestedModelForm, wrapping it in a nested node" % child_form_name)
                    nodelist.append(NestedFormNode(child_form_name, child_form_helper_name, top_level=False))
                else:
                    print(" %s (%s) is NOT a NestedModelForm, wrapping it in a crispy node" % (child_form_name, child_form.__class__))
                    nodelist.append(CrispyFormNode(child_form_name, 
                        child_form_helper_name if hasattr(child_form, "helper") else None))

            # We need to print the management form
            management_form_helper = FormHelper()
            management_form_helper.form_tag = False
            management_form_helper.disable_csrf = True
            management_form = actual_form.management_form

            context["%s_management_form" % form_name] = management_form
            context["%s_management_form_helper" % form_name] = management_form_helper
            # Place a data binding on the management form for KnockoutJS
            fields = management_form.fields
            fields["TOTAL_FORMS"].widget.attrs["data-bind"] = "value: totalForms"
            fields["INITIAL_FORMS"].widget.attrs["data-bind"] = "value: initialForms"
            fields["MAX_NUM_FORMS"].widget.attrs["data-bind"] = "value: maxForms"

            # Let Crispy handle the printing of this...
            print("Adding %s management_form to the node list" % form_name)
            nodelist.append(CrispyFormNode("%s_management_form" % form_name,
                "%s_management_form_helper" % form_name))
        else:
            """ We have two cases to deal with here:
                - BlockForm - it has an inline form that we need to print here
                - TenantForm - no inline form to worry about...

                If it has an inline form, note that we need to make a NestedModelNode
            """
            if hasattr(actual_form, "inline_form"):
                context["%s_inline_form" % form_name] = actual_form.inline_form
                nodelist.append(NestedFormNode("%s_inline_form" % form_name, self.helper, top_level=False))

        # Check if there is an inline form
        if hasattr(actual_form, "inline_actions_form") and \
                actual_form.inline_actions_form is not None:
            context["inline_actions_form"] = actual_form.inline_actions_form
            nodelist.append(CrispyFormNode(form="inline_actions_form", helper=self.helper))


        # Add a DIV for the children
        children_div_class = "%s_children_div" % form_name
        nodelist.append(HtmlContent("<div class='%s'>" % children_div_class))
        # Current KIDS should be printed here BTW
        nodelist.append(HtmlContent("</div>"))

        nodelist.append(HtmlContent("</div>"))

        if top_level:
            # print out ALL the script templates
            nodelist.append(KnockoutFormTemplate(self.form))

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
