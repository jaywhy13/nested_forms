

function ManagementForm(parentFormName, childTemplateForm){
    this.childTemplateForm = childTemplateForm; // BuildingForm-template
    this.parentFormName = parentFormName;
    this.childrenDivFormName = this.parentFormName + "_children_div";

    // Declare some observables
    this.totalForms = ko.observable(0);
    this.maxForms = ko.observable(0);
    this.initialForms = ko.observable(0);
}

ManagementForm.prototype.addChildForm = function() {
    // Adds a child form to this form
    var div = jQuery("<div/>");
    div.attr("data-bind", "template: " + this.childTemplateForm);
    div.appendTo(jQuery("." + this.childrenDivFormName));
    //console.log(div.get()[0]);
    // ko.applyBindings(this, div.get()[0]);
    // this.totalForms( this.totalForms() + 1 );
};

