
/**
 * The Management Form manages bindings for Django formset management forms.
 * The Django management form stores the following information:
 * - maximum number of forms addable 
 * - total of forms currently added (TOTAL_FORMS)
 * - total number of initial forms 
 * So basically, we want to use KnockoutJS to update the TOTAL_FORMS variable.
 * This scope provides an "addChild" function that can be called within the
 * scope of a management form binding to add a child form. 
 * In order to achieve this we take as input, the parentFormName, childTemplate 
 * name, the number of initial forms and also the prefix. 
 *
 * Now, every time we add a new management form, we actually need to call 
 * applyBindings on the entire structure that is being added because we actually
 * need KnockoutJS to translate some of the bidnings into actual properties. 
 *
 * We need to do this because the templates can't store the 'prefix' of the 
 * element before hand. So the field for TOTAL_FORMS could be called
 * buildings-0-TOTAL_FORMS or buildings-1-TOTAL_FORMS depending on which child 
 * it is and so on. So we have to apply bindings to get those variables put in.
 *
 * This works fine when the page is loading. We just apply the bindings to the 
 * management form div container which also has the actions form. We needed to 
 * put the actions form in that div because more than likely the actions will
 * need to call addChild or access something else in that scope. 
 *
 * Now we need to add a child....
 * In order to add a child, 
 * 
 * 
 * @param {[type]} parentFormName [description]
 * @param {[type]} childTemplate  [description]
 * @param {[type]} initialForms   [description]
 * @param {[type]} prefix         [description]
 */
function ManagementForm(parentFormName, childTemplate, initialForms, childPrefix){
    // e.g. BlockForm-form, BuildinForm-template, x, buildings
    // e.g. BuildingForm-form-buildings-0, TenantForm-template, x, buildings-0-tenants
    
    var self = this;
    self.childTemplate = childTemplate; // BuildingForm-template
    self.parentFormName = parentFormName;
    self.childrenDivFormName = self.parentFormName + "_children_div";
    self.childPrefix = childPrefix;

    // Declare some observables
    self.totalForms = ko.observable(initialForms);
    self.maxForms = ko.observable(1000);
    self.initialForms = ko.observable(initialForms);

    self.addChildForm = function() {
        console.log("Adding child " + this.childTemplate + " to " + this.childrenDivFormName + " with childPrefix: " + this.childPrefix, " parent is: ", this.parentFormName);

        // Adds a child form to this form
        var div = jQuery("<div/>");
        div.attr("data-bind", "template: {name: '" + self.childTemplate + "'}");
        div.addClass("child-form-wrapper");
        div.appendTo(jQuery("#" + self.childrenDivFormName));
        if($("#" + self.childrenDivFormName).length == 0){
            console.log("Warning: " + this.childrenDivFormName + " container does not exist");
        }

        console.log(div.get()[0]);
        self.totalForms( self.totalForms() + 1 );
        // Setup bindings for the grand child management form
        var formName = this.parentFormName.split("-")[0];
        var childForm = getChildFormName(formName);
        var childFormName = childForm + "-form-" + self.childPrefix + "-0";
        var grandChildTemplate = getChildTemplateName(childForm);
        var grandChildManagementFormDivId = childFormName + "_management_form_div";
        var grandChildPrefix = getChildRelName(childForm);

        var grandChildManagementForm = new ManagementForm(childFormName, 
            grandChildTemplate, 0, grandChildPrefix);
        grandChildManagementForm.index = self.totalForms();
        grandChildManagementForm.prefix = self.childPrefix;

        ko.applyBindings(grandChildManagementForm, div.get()[0]);
        //console.log("Data for: ", ko.dataFor(div.get()[0]));
        //console.log("Context for: ", ko.dataFor(div.get()[0]));

    };
}

/**
 * Returns the name of the child template given the name of the form class (parent)
 * @param  {String} parentForm 
 * @return {String} - the name of the template
 */
function getChildTemplateName(parentForm){
    return childInfos[parentForm]["childTemplate"];
}

/**
 * Returns the name of the child form class
 * @param  {String} parentForm 
 * @return {String} - the name of the child form
 */
function getChildFormName(parentForm){
    return childInfos[parentForm]["childForm"];
}

function getChildRelName(parentForm){
    return childInfos[parentForm]["relName"];
}


