

function ManagementForm(parentFormName, childTemplate, initialForms){
    
    var self = this;
    self.childTemplate = childTemplate; // BuildingForm-template
    self.parentFormName = parentFormName;
    self.childrenDivFormName = self.parentFormName + "_children_div";

    // Declare some observables
    self.totalForms = ko.observable(initialForms);
    self.maxForms = ko.observable(1000);
    self.initialForms = ko.observable(initialForms);

    self.addChildForm = function() {
        // Adds a child form to this form
        var div = jQuery("<div/>");
        div.attr("data-bind", "template: {name: '" + self.childTemplate + "', data: {index: " + self.totalForms() + "}}");
        div.appendTo(jQuery("." + self.childrenDivFormName));
        self.totalForms( self.totalForms() + 1 );
        ko.applyBindings(this, div.get()[0]);
    };
}


