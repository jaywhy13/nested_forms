import json

from django.template import Node, NodeList
from django import template
from django.utils.safestring import mark_safe
from django.forms.formsets import BaseFormSet

from crispy_forms.helper import FormHelper
from crispy_forms.templatetags.crispy_forms_tags import CrispyFormNode

from nest.forms import NestedModelForm

register = template.Library()

def get_form_template_name(form):
    if isinstance(form, type):
        form = form()
    return "%s-template" % form.__class__.__name__

def get_management_form_div_name(form):
    return "%s-management-form-div" % get_form_name(form)

def get_form_name(form):
    """ Use a unified form naming function that names forms and base formsets.
        Forms are named which include their prefix to avoid clashes with 
        other forms in the context.
        Note that we don't have to worry about this since there will only ever
        be one base formset per level so there's no risk of clashing with 
        other formsets in the context.
        The base formset is therefore named simply by using the class name of 
        the form it holds. 
    """
    is_formset = issubclass(form.__class__, BaseFormSet)
    if not is_formset:
        if isinstance(form, type): # if it's a class, just return the name
            return form.__name__
        form_name = "%s-form-%s" % (form.__class__.__name__, 
            form.prefix) if form.prefix else \
            "%s-form" % (form.__class__.__name__)
    else:
        form_name = "%s-formset" % form.form.__name__
    return form_name

def get_default_helper():
    helper = FormHelper()
    process_helper(helper)
    return helper

def process_helper(helper):
    helper.form_tag = False


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

        # Loop through each and get the knockout templates for each
        for child_form, parent_form in child_forms:
            child_form = child_form() if isinstance(child_form, type) else child_form
            # Add knockoutjs bindings to the child form fields
            for field_name, field in child_form.fields.iteritems():
                attr = "{'id' : 'id_' + prefix + '-' + index + '-%s', 'name' : prefix + '-' + index + '-%s'}" % (field_name, field_name)
                field.widget.attrs["data-bind"] = mark_safe("attr: %s" % attr)
            form_name = get_form_name(child_form)
            template_name = get_form_template_name(child_form)
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
                    attr = "{'id' : 'id_' + prefix + '-' + index + '-%s-%s', 'name' : prefix + '-' + index + '-%s-%s'}" % (child_prefix, field_name, child_prefix, field_name)
                    field.widget.attrs["data-bind"] = mark_safe("attr: %s" % attr)
                context["child_%s_management_form" % form_name] = grand_child_management_form
                context["child_%s_management_form_helper" % form_name] = get_default_helper()
                nodelist.append(CrispyFormNode("child_%s_management_form" % form_name, 
                    "child_%s_management_form_helper" % form_name))
            nodelist.append(HtmlContent("</script>"))
        return nodelist.render(context)


def get_bindings(form):
    if not hasattr(form, "inline_form"):
        return []

    formset = form.inline_form
    form_name = get_form_name(form)
    child_template_name = get_form_template_name(formset.form)
    parent_form_div_class = "%s_form_div" % form_name
    num_forms = len(formset.forms)
    management_form_div_class = get_management_form_div_name(formset.parent_form)
    prefix = formset.prefix

    bindings = []

    bindings.append(
        """
            ko.applyBindings(new ManagementForm('%s', '%s', %s, '%s'), jQuery(".%s").get()[0]);
        """ % (form_name, child_template_name, num_forms, prefix, management_form_div_class)
    )

    for child_form in formset.forms:
        child_bindings = get_bindings(child_form)
        for child_binding in child_bindings:
            bindings.append(child_binding)

    return bindings


class NestedFormNodeJs(Node):
    """ This is node for printing out the JS code to activate knockout for the 
        management form.
    """
    def __init__(self, form):
        self.form = form
        self.form_var = template.Variable(form)

    def render(self, context):
        actual_form = self.form_var.resolve(context)
        bindings = get_bindings(actual_form)
        #bindings.reverse() # bind in reverse order ...
        nodelist = NodeList()

        # Add the script to activate this form
        nodelist.append(HtmlContent("""
            <script> 
                $(document).ready(function(){
                    // new ManagementForm(parentForm, childTemplate, initialForms);
                    %s
                });
            </script>
            """ % "\n".join(bindings)))
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
        form_name = get_form_name(actual_form) if not is_formset else get_form_name(actual_form.parent_form)
        #print("== Rendering %s (Formset: %s) " % (form_name, is_formset))
        if self.helper is not None:
            actual_helper = self.helper_var.resolve(context)
        else:
            actual_helper = get_default_helper() if not hasattr(actual_form, 'helper') \
                else actual_form.helper

        if actual_helper.form_tag:
            actual_helper.form_tag = False
            #raise template.TemplateSyntaxError("form_tag cannot be True on the helper, please go and rectify that")

        # Place a link on the formset back to its parent form
        if not is_formset and hasattr(actual_form, "inline_form"):
            actual_form.inline_form.parent_form = actual_form

        """ Basically we create a node list and all the following things to it:
            - <div class='FormName_form_div'> - HtmlContent
                - The actual form (parent)
                -  The inline form which prints the children and management form (hidden) 
                - <div class='FormName_children_div'></div>
                - Inline actions form (if one exists)
                - <script>Knockout form templates</script>
            - </div>
            Then we return nodelist.render
        """

        # Add the forms to the nodelist
        nodelist = NodeList()
        # Add the main form to our node list

        # === PRINT THE PARENT FORM
        if not is_formset:
            form_div_class = "%s_form_div" % form_name
            #print("Creating form div class: %s" %form_div_class)
            nodelist.append(HtmlContent("<div class='%s form-container'>" % form_div_class))
            nodelist.append(CrispyFormNode(form=self.form, helper=self.helper))

        # === PRINT THE KIDS
        if is_formset: # e.g. BuildingFormSet
            # We need to add each form AND print the management form
            # Add a DIV for the children
            children_div_class = "%s_children_div" % form_name
            nodelist.append(HtmlContent("<div class='%s'>" % children_div_class))
            for child_index in range(len(actual_form.forms)):
                child_form = actual_form.forms[child_index]
                if not hasattr(child_form, "helper"):
                    child_form.helper = get_default_helper()
                child_form_name = "%s_%s" % (get_form_name(child_form), child_index)
                #print(" Adding %s to the nodelist" % child_form_name)
                child_form_helper_name = "%s_helper" % child_form_name
                context[child_form_name] = child_form
                context[child_form_helper_name] = child_form.helper
                process_helper(child_form.helper)
                if hasattr(child_form, "inline_form"):
                    #print(" %s is a NestedModelForm, wrapping it in a nested node" % child_form_name)
                    nodelist.append(NestedFormNode(child_form_name, child_form_helper_name, top_level=False))
                else:
                    #print(" %s (%s) is NOT a NestedModelForm, wrapping it in a crispy node" % (child_form_name, child_form.__class__))
                    nodelist.append(CrispyFormNode(child_form_name, 
                        child_form_helper_name))
            nodelist.append(HtmlContent("</div>"))

            # We need to print the management form for these kids
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
            #print("Adding %s management_form to the node list" % form_name)
            # Add a div for the management form
            management_form_div_class = get_management_form_div_name(actual_form.parent_form)
            nodelist.append(HtmlContent("<div class='%s'>" % management_form_div_class))
            nodelist.append(CrispyFormNode("%s_management_form" % form_name,
                "%s_management_form_helper" % form_name))

            # Check if there is an inline form
            if hasattr(actual_form, "actions_form") and \
                    actual_form.actions_form is not None:
                inline_actions_form_name = "%s-inline_actions_form" % get_form_name(actual_form.actions_form)
                inline_actions_form_helper_name = "%s-helper" % inline_actions_form_name
                context[inline_actions_form_name] = actual_form.actions_form
                context[inline_actions_form_helper_name] = actual_form.actions_form().helper
                nodelist.append(CrispyFormNode(form=inline_actions_form_name, 
                    helper=inline_actions_form_helper_name))
            nodelist.append(HtmlContent("</div>"))

        else: # not a formset
            """ We have two cases to deal with here:
                - BlockForm - it has an inline form that we need to print here
                - TenantForm - no inline form to worry about...

                If it has an inline form, note that we need to make a NestedModelNode
            """
            if hasattr(actual_form, "inline_form"):
                context["%s_inline_form" % form_name] = actual_form.inline_form
                nodelist.append(NestedFormNode("%s_inline_form" % form_name, self.helper, top_level=False))



        if not is_formset:
            # we didn't add this if it was a formset
            nodelist.append(HtmlContent("</div>")) # for the form

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
