Django Nested Forms Example
============
This project is a complete example of how to get nested forms working in Django. It provides the following features:
- Automatic rendering of nested forms via the use of the nest_crispy form template tag.
- Addition of child forms dynamically
- Removal of child forms (NOT YET IMPLEMENTED)

# Requirements
- Python 2.7
- Node and NPM

# Installation
The following commands can be used to install the app if you want to try it out.
```
git checkout http://github.com/jaywhy13/nested_forms.git
virtualenv nested_forms # create a virtual env
cd nested_forms
source bin/activate # source the virtual env
pip install -r requirements.txt

# Install DustJS via Node
cd node
npm install watch
npm install dustjs-linkedin
cd ..

./manage.py syncdb

# Run the server and git it a tryout...
./manage.py runserver 
```


# Dependencies
- Django 1.5.5
- Crispy Forms

# Overview
The project provides a `NestedModelForm` class that is to be extended by all forms that will have children. One needs to override the constructor to provide information about the form that needs to be nested. As seen below in the constructor for `BlockForm`, you can see that the `"child_form"` key word argument is set before the call to super. 

```
# models.py
from django.db import models

class Block(models.Model):
	name = models.CharField("Block Name", max_length=255)


class Building(models.Model):
	name = models.CharField("Bldg Name", max_length=255)
	block = models.ForeignKey("Block", blank=True, null=True, 
		related_name="buildings")

class Tenant(models.Model):
	first_name = models.CharField(max_length=255)
	last_name = models.CharField(max_length=255)
	building = models.ForeignKey("Building", blank=True, null=True, 
		related_name="tenants")


# forms.py
class BuildingForm(NestedModelForm):

	def __init__(self, *args, **kwargs):
	  # Setup our helper
		super(BuildingForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.form_method = 'post'

	class Meta:
		model = Building		
		exclude = ["block"]


class BlockForm(NestedModelForm):
	def __init__(self, *args, **kwargs):
		kwargs["child_form"] = BuildingForm # indicate that we want to nest BuildingForm
		super(BlockForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_tag = False
		self.helper.add_input(Submit("submit", "Create Building"))

	class Meta:
		model = Block

```

This project provides a management command to generates DustJS templates. Therefore, running the following command will generate the templates in a `form_templates` folder at the `settings.PROJECT_ROOT`. It searches all apps in `INSTALLED_APPS` for forms that extend `NestedModelForm` that have children and generates a template for that child (we only need Dust templates for the children, since we'll be adding those dynamically). 

```
./manage.py form_templates
```

The final step is to generate a `templates.js` that needs to be included on the page so that Dust can access the templates. This is achieved simply by running the following command from the root of the project. 
```
node node/dustify.js
```
