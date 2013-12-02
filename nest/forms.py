from django.forms import ModelForm, Form
from django.forms.models import (
	modelformset_factory,
	inlineformset_factory,
	BaseInlineFormSet
)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Button

from nest.models import Building, Block, Tenant

class NestedModelForm(ModelForm):

	def __init__(self, *args, **kwargs):
		child_form = kwargs.pop("child_form", None)
		child_actions_form = kwargs.pop("child_actions_form", None)
		super(NestedModelForm, self).__init__(*args, **kwargs)
		if child_form:
			self.setup_nested_form(child_form, child_actions_form)

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
			TODO: This form has NO prefix, so the children has a 'None' in
			their name, need to fix that.
			TODO: Sort out how child_actions_form will call JS function
			TODO: Think about nesting a form within a InlineFormset
			TODO: form_templates command needs some work. Need to figure out 
			how we will print the form without nesting them.
		"""
		parent_model = self._meta.model
		child_model = child_form._meta.model
		InlineFormset = inlineformset_factory(parent_model, child_model, 
			extra=0)
		self.inline_form = InlineFormset(
			instance=self.instance,
			data=self.data if self.is_bound else None,
			prefix="%s-%s" % (
				self.prefix,
				InlineFormset.get_default_prefix()
				)
			)
		self.inline_actions_form = child_actions_form

	@staticmethod
	def get_add_child_js(form):
		""" Returns the JS call necessary to add a child to this form of type:
			form
		"""
		return "addChildForm()"

	@staticmethod
	def get_delete_child_js():
		""" Returns the JS call necessary to delete a child form from this form
		"""
		return "deleteChild(this)"

class BlockActionsForm(Form):

	def __init__(self, *args, **kwargs):
		super(BlockActionsForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		# Make sure that the form tag is set to False
		self.helper.form_tag = False
		# Add a button to add a building
		self.helper.add_input(Button("add_building", "Add Building",
			onclick="%s" % NestedModelForm.get_add_child_js(BlockForm)))

class BlockForm(NestedModelForm):
	def __init__(self, *args, **kwargs):
		# Set the child form
		kwargs["child_form"] = BuildingForm
		kwargs["child_actions_form"] = BlockActionsForm
		super(BlockForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_tag = False

	class Meta:
		model = Block

class BuildingForm(ModelForm):

	def __init__(self, *args, **kwargs):
		super(BuildingForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.form_method = 'post'

	class Meta:
		model = Building		

class TenantForm(ModelForm):
	class Meta:
		model = Tenant

BuildingFormSet = modelformset_factory(Building, form=BuildingForm, extra=3)
TenantFormSet = modelformset_factory(Tenant, form=TenantForm)
InlineFormset = inlineformset_factory(Block, Building, extra=1)

class BaseNestedFormset(BaseInlineFormSet):
	
	def add_fields(self, form, index):
		super(BaseNestedFormset, self).add_fields(form, index)

		form.nested = self.nested_formset_class(
			instance=form.instance,
			data=form.data if form.is_bound else None,
			prefix="%s-%s" % (
				form.prefix,
				self.nested_formset_class.get_default_prefix()
				)
			)

	def is_valid(self):
		""" Check if the other nested forms are valid as well
		"""
		result = super(BaseNestedFormset, self).is_valid()
		print("Start result = %s" % result)
		for form in self.forms:
			result = result and form.nested.is_valid()
			print("Is %s valid? %s" % (form.__class__, result))

		return result

	def save(self, commit=True):
		print("Saving main form")
		result = super(BaseNestedFormset, self).save(commit=commit)

		for form in self.forms:
			form.nested.save(commit=commit)
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
		extra=1
		)
	return parent_child
