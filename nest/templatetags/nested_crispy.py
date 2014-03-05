import json

from django.template import Node, NodeList
from django import template
from django.utils.safestring import mark_safe
from django.forms.formsets import BaseFormSet

from crispy_forms.helper import FormHelper
from crispy_forms.templatetags.crispy_forms_tags import CrispyFormNode

from nest.forms import NestedModelForm

register = template.Library()

""" 
    All the nested forms we print out will have this general structure
    - <div id='{form_name}_form_div' class='form-container'> - HtmlContent
        - Fields from the parent form 
        -  The inline form which prints the children and management form (hidden) 
        - <div id='{form_name}_children_div' class='form-children'>
            --- Kids printed here ---
          </div>
        - <div id='{form_name}_management_form_div' class='management-form-div'>
            - Management form (hidden)
            - Inline actions form (if one exists)
        - </div>
    - </div>
"""


def get_form_template_name(form):
    if isinstance(form, type):
        form = form()
    return "%s-template" % form.__class__.__name__

def get_management_form_div_name(form, prefix=""):
    return "%s_management_form_div" % get_form_name(form, prefix=prefix)

def get_form_name(form, prefix=""):
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
        if form.prefix:
            prefix = form.prefix
        form_name = "%s-form-%s" % (form.__class__.__name__, prefix) if prefix \
            else "%s-form" % (form.__class__.__name__)
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

        """ 
            All the nested forms we print out will have this general structure
            - <div id='{form_name}_form_div' class='form-container'> - HtmlContent
                - Fields from the parent form 
                -  The inline form which prints the children and management form (hidden) 
                - <div id='{form_name}_children_div' class='form-children'>
                    --- Kids printed here ---
                  </div>
                - <div id='{form_name}_management_form_div' class='management-form-div'>
                    - Management form (hidden)
                    - Inline actions form (if one exists)
                - </div>
            - </div>
        """

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
            context["child_%s_helper" % form_name] = (child_form.helper if \
               hasattr(child_form, "helper") else None) or get_default_helper()

            # print out the script for the template
            nodelist.append(HtmlContent('<script type="text/html" id="%s">' % template_name))
            form_container_attrs = "{'id': '%s_form_div' }" % get_form_name(child_form, prefix="' + prefix + '-' + index + '")
            nodelist.append(HtmlContent('<div data-bind="attr: %s" class="form-container">' % mark_safe(form_container_attrs)))
            nodelist.append(CrispyFormNode(form="child_%s" % form_name, 
                helper="child_%s_helper" % form_name))
            if hasattr(child_form, "inline_form"): # then print the management form as well
                """ If our child has a child (e.g. building has tenants)
                    then print the management form for it's child (tenant)
                """
                # first we need to actually print the div to hold the kids
                form_children_attrs = "{'id': '%s_children_div' }" % \
                    get_form_name(child_form, prefix="' + prefix + '-' + index +'")        
                nodelist.append(HtmlContent("""
                    <div data-bind="attr: %s" class="form-children"></div>
                """ % mark_safe(form_children_attrs)))

                management_form_div_class = get_management_form_div_name(parent_form, prefix="' + prefix + '-' + index + '")
                management_form_div_attrs = "{'id' : '%s'}" % management_form_div_class
                nodelist.append(HtmlContent("""
                    <div data-bind="attr: %s" class='management-form-div'>
                    """ % management_form_div_attrs))

                formset = child_form.inline_form
                grand_child_management_form = child_form.inline_form.management_form

                # Tweak it and adds Knockout bindings 
                parent_prefix = parent_form.inline_form.prefix
                child_prefix = child_form.inline_form.prefix
                fields = grand_child_management_form.fields
                for field_name, field in fields.iteritems():
                    attr = "{'id' : 'id_' + prefix + '-' + index + '-%s-%s', 'name' : prefix + '-' + index + '-%s-%s'}" % (child_prefix, field_name, child_prefix, field_name)
                    if field_name == "TOTAL_FORMS":
                        attr = "{'id' : 'id_' + prefix + '-' + index + '-%s-%s', 'name' : prefix + '-' + index + '-%s-%s', 'value': totalForms }" % (child_prefix, field_name, child_prefix, field_name)
                    field.widget.attrs["data-bind"] = mark_safe("attr: %s" % attr)
                context["child_%s_management_form" % form_name] = grand_child_management_form
                context["child_%s_management_form_helper" % form_name] = get_default_helper()
                nodelist.append(CrispyFormNode("child_%s_management_form" % form_name, 
                    "child_%s_management_form_helper" % form_name))

                if hasattr(formset, "actions_form") and \
                        formset.actions_form is not None:
                    inline_actions_form_name = "%s-inline_actions_form" % get_form_name(child_form)
                    inline_actions_form_helper_name = "%s-helper" % inline_actions_form_name
                    context[inline_actions_form_name] = formset.actions_form
                    context[inline_actions_form_helper_name] = formset.actions_form().helper
                    nodelist.append(CrispyFormNode(form=inline_actions_form_name, 
                        helper=inline_actions_form_helper_name))
                
                nodelist.append(HtmlContent("</div>")) # end of the management form div
            nodelist.append(HtmlContent("</div>")) # end of form-cotnainer

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
            // Management form for the children of %s
            ko.applyBindings(new ManagementForm('%s', '%s', %s, '%s'), jQuery("#%s").get()[0]);
        """ % (form_name, form_name, child_template_name, num_forms, prefix, management_form_div_class)
    )

    for child_form in formset.forms:
        child_bindings = get_bindings(child_form)
        for child_binding in child_bindings:
            bindings.append(child_binding)

    return bindings


def get_js_info(form):
    """ Returns a list of assignments that indicate the name of the 
        child template and child form name given a form name
    """
    infos = {}
    while hasattr(form, "child_form"):
        info = dict(childTemplate="%s-template" % get_form_name(form.child_form),
            childForm="%s" % get_form_name(form.child_form),
            relName=form.inline_form.rel_name
            )
        infos[get_form_name(form.__class__)] = info
        form = form.child_form()
    return """
        var childInfos = %s;
    """ % json.dumps(infos)


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

        js_info = get_js_info(actual_form)

        # Add the script to activate this form
        nodelist.append(HtmlContent("""
            <script> 
                %s 

                $(document).ready(function(){
                    // new ManagementForm(parentForm, childTemplate, initialForms);
                    %s
                });
            </script>
            """ % (js_info, "\n".join(bindings))))
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
            - <div id='{form_name}_form_div' class='form-container'> - HtmlContent
                - Fields from the parent form 
                -  The inline form which prints the children and management form (hidden) 
                - <div id='{form_name}_children_div' class='form-children'>
                    --- Kids printed here ---
                  </div>
                - <div id='{form_name}_management_form_div' class='management-form-div'>
                    - Management form (hidden)
                    - Inline actions form (if one exists)
                - </div>
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
            nodelist.append(HtmlContent("<div id='%s' class='form-container'>" % form_div_class))
            nodelist.append(CrispyFormNode(form=self.form, helper=self.helper))

        # === PRINT THE KIDS
        if is_formset: # e.g. BuildingFormSet
            # We need to add each form AND print the management form
            # Add a DIV for the children
            children_div_class = "%s_children_div" % form_name
            nodelist.append(HtmlContent("<div id='%s' class='form-children'>" % children_div_class))
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
            nodelist.append(HtmlContent("<div id='%s' class='management-form-div'>" % management_form_div_class))
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
