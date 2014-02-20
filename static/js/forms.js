

function ManagementForm(parentFormName, childTemplateForm){
    var self = this;
    self.childTemplateForm = childTemplateForm; // BuildingForm-template
    self.parentFormName = parentFormName;
    self.childrenDivFormName = self.parentFormName + "_children_div";

    // Declare some observables
    self.totalForms = ko.observable(0);
    self.maxForms = ko.observable(1000);
    self.initialForms = ko.observable(0);

    self.addChildForm = function() {
        // Adds a child form to this form
        console.log("Adding a child");
        var div = jQuery("<div/>");
        div.attr("data-bind", "template: {name: '" + self.childTemplateForm + "', data: {index: " + self.totalForms() + "}}");
        div.appendTo(jQuery("." + self.childrenDivFormName));
        self.totalForms( self.totalForms() + 1 );
        ko.applyBindings(this, div.get()[0]);
    };


}


