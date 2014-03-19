import inspect
import re

from django.forms import ModelForm, Form, HiddenInput
from django.forms.models import (
	modelformset_factory,
	inlineformset_factory,
	BaseInlineFormSet
)
from django import forms
from django.utils import html

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Button

from nest.models import Building, Block, Tenant, Furniture


class SubmitButtonWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        return '<input type="button" name="%s" value="%s" onclick="deleteChild(this);">' % (html.escape(name), html.escape(value))

class SubmitButtonField(forms.Field):
    def __init__(self, *args, **kwargs):
        if not kwargs:
            kwargs = {}
        kwargs["widget"] = SubmitButtonWidget

        super(SubmitButtonField, self).__init__(*args, **kwargs)

    def clean(self, value):
        return value

def to_underscore_case(name):
	""" Converts title case to underscore case
	"""
	s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
	return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()



class NestedModelForm(ModelForm):

	def __init__(self, *args, **kwargs):
		child_form = kwargs.pop("child_form", None)
		child_actions_form = kwargs.pop("child_actions_form", None)
		super(NestedModelForm, self).__init__(*args, **kwargs)
		if not self.prefix:
			self.prefix = ""
		self.setup_nested_form(child_form, child_actions_form)

	def get_uc_form_name(self):
		""" Returns the underscore cased version
		"""
		return to_underscore_case(self.get_form_name())

	def is_valid(self):
		valid = super(NestedModelForm, self).is_valid()
		# Check if the inline form is valid
		if self.inline_form:
			valid &= self.inline_form.is_valid()
		return valid

	def save(self, commit=True, save_formset=True):
		result = super(NestedModelForm, self).save(commit=commit)

		if self.inline_form:
			if save_formset:
				self.inline_form.save(commit=commit)
		return result

	def setup_nested_form(self, child_form, child_actions_form=None):
		""" This function declares a property "inline_form" that contains
			the inline formset (generated using the inlineformset_factory).
			Additionally, if the user had supplied a "cihld_actions_form" 
			that is also setup under the "inline_actions_form" property.
			This is done so that the nested_form template tag can 
			search for both these properties and create the necessary template
			Crispy Nodes so that Django can render them normally. 
			Finally, key thing to note here is that this method also
			ensures that data is passed to the child form so that it 
			renders the appropriate data is the form is already bound.
			TODO: Think about nesting a form within a InlineFormset
			TODO: Removal of forms... the delete button not showing up
			TODO: SUbmission of data, the submit buttons are going to appear some
			where else basically. 
			TODO: Add the radio button logic
		"""
		self.parent_model = self._meta.model # this form 
		self.child_model = child_form._meta.model if child_form else None
		self.child_form = child_form
		self.child_actions_form = child_actions_form
		self.inline_prefix = None
		if child_form:
			InlineFormset = inlineformset_factory(self.parent_model, 
				self.child_model, extra=0,
				formset=ManangeFormCachedBaseInlineFormset,
				form=child_form)
			prefix_separator = "-" if self.prefix else ""
			self.inline_form = InlineFormset(
				instance=self.instance,
				data=self.data if self.is_bound else None,
				prefix = "%s%s%s" % (
					self.prefix,
					prefix_separator,
					InlineFormset.get_default_prefix()
					)
				)
			self.inline_form.actions_form = child_actions_form
			self.inline_prefix = InlineFormset.get_default_prefix()
		else:
			self.inline_form = None
			self.inline_actions_form = None

	@staticmethod
	def get_add_child_js(child_form, parent_form):
		""" Returns the JS call necessary to add a child to this form of type
			"child_form" to a given form. Also need to specify the parent_form.
		"""
		if inspect.isclass(child_form):
			child_form = child_form()
		if inspect.isclass(parent_form):
			parent_form = parent_form()
		return "click: addChildForm"
		# % (child_form.get_form_name(), parent_form.inline_prefix)

	@staticmethod
	def get_delete_child_js():
		""" Returns the JS call necessary to delete a child form from this form
		"""
		return "deleteChild(this)"

class BuildingActionsForm(Form):

	def __init__(self, *args, **kwargs):
		super(BuildingActionsForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		# Make sure that the form tag is set to False
		self.helper.form_tag = False
		# Add a button to add a building
		self.helper.add_input(Button("add_building", "Add Building",
			data_bind="%s" % NestedModelForm.get_add_child_js(BuildingForm,
				BlockForm)))

class BlockForm(NestedModelForm):
	def __init__(self, *args, **kwargs):
		# Set the child form
		kwargs["child_form"] = BuildingForm
		kwargs["child_actions_form"] = BuildingActionsForm
		super(BlockForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_tag = False
		self.helper.add_input(Submit("submit", "Create Block"))

	class Meta:
		model = Block

class BuildingForm(NestedModelForm):

	def __init__(self, *args, **kwargs):
		kwargs["child_form"] = TenantForm
		kwargs["child_actions_form"] = TenantActionsForm
		super(BuildingForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.form_method = 'post'
		self.helper.add_input(Submit("submit", "Create Building"))

	class Meta:
		model = Building		
		exclude = ["block"]

class TenantActionsForm(Form):

	def __init__(self, *args, **kwargs):
		super(TenantActionsForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		# Make sure that the form tag is set to False
		self.helper.form_tag = False
		# Add a button to add a building
		self.helper.add_input(Button("add_tenant", "Add Tenant",
			data_bind="%s" % NestedModelForm.get_add_child_js(TenantForm,
				BuildingForm)))


class TenantForm(NestedModelForm):

	def __init__(self, *args, **kwargs):
		kwargs["child_form"] = FurnitureForm
		super(TenantForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.form_method = 'post'
		self.helper.add_input(Submit("submit", "Create Tenant"))

	class Meta:
		model = Tenant
		exclude = ["building"]

class FurnitureForm(ModelForm):
	class Meta:
		model = Furniture

BuildingFormSet = modelformset_factory(Building, form=BuildingForm, extra=0)
TenantFormSet = modelformset_factory(Tenant, form=TenantForm)
InlineFormset = inlineformset_factory(Block, Building, extra=0)

class BaseNestedFormset(BaseInlineFormSet):

	def __init__(self, *args, **kwargs):
		super(BaseNestedFormset, self).__init__(*args, **kwargs)
		for form in self.forms:
			form.fields["DELETE"].widget = HiddenInput()
			form.fields["delete_button"] = SubmitButtonField(initial="Delete")

	def add_fields(self, form, index):
		super(BaseNestedFormset, self).add_fields(form, index)

	def is_valid(self):
		""" Check if the other nested forms are valid as well
		"""
		result = super(BaseNestedFormset, self).is_valid()
		for form in self.forms:
			result = result and form.inline_form.is_valid() if hasattr(form, "inline_form") else result
			#print("  Is %s valid? %s" % (form.__class__.__name__, result))
		return result

	def save(self, commit=True):
		result = super(BaseNestedFormset, self).save(commit=commit)
		# for form in self.forms:
		# 	if hasattr(form, "inline_form"):			
		# 		form.inline_form.save(commit=commit)
		cleaned_datas = self.cleaned_data
		for i in range(len(self.forms)):
			form = self.forms[i]
			cleaned_data = cleaned_datas[i]
			save_formset = not cleaned_data.get("DELETE")
			if hasattr(form, "inline_form"):
				form.inline_form.save(commit=commit, save_formset=save_formset)
				#print("Saving form: %s" % form.__class__.__name__)
		return result

def nested_formset_factory(parent_model, child_model, grandchild_model=None):
	""" Create a formset factory that handles a 3-level relationship
	"""
	parent_child = inlineformset_factory(
		parent_model,
		child_model,
		formset=BaseNestedFormset,
		extra=1
		)

	parent_child.nested_formset_class = inlineformset_factory(
		child_model,
		grandchild_model,
		formset=BaseNestedFormset,
		extra=1
		)
	return parent_child

class ManangeFormCachedBaseInlineFormset(BaseNestedFormset):

	@property
	def management_form(self):
		if not hasattr(self, "_management_form"):
			self._management_form = super(ManangeFormCachedBaseInlineFormset, self).management_form
		return self._management_form

	def save(self, commit=True, save_formset=True):
		if save_formset:
			super(ManangeFormCachedBaseInlineFormset, self).save(commit=commit)

