

function ManagementForm(parentFormName, childTemplate, initialForms, prefix){

    
    var self = this;
    self.childTemplate = childTemplate; // BuildingForm-template
    self.parentFormName = parentFormName;
    self.childrenDivFormName = self.parentFormName + "_children_div";
    self.prefix = prefix;

    // Declare some observables
    self.totalForms = ko.observable(initialForms);
    self.maxForms = ko.observable(1000);
    self.initialForms = ko.observable(initialForms);

    self.addChildForm = function() {
        console.log("Adding child " + this.childTemplate + " to " + this.childrenDivFormName);
        // Adds a child form to this form
        var div = jQuery("<div/>");
        var templateData = {
            name : self.childTemplate,
            data : {
                index: self.totalForms(),
                prefix : self.prefix
            }
        };
        div.attr("data-bind", "template: " + JSON.stringify(templateData));
        div.appendTo(jQuery("." + self.childrenDivFormName));
        if($("." + self.childrenDivFormName).length == 0){
            console.log("Warning: " + this.childrenDivFormName + " container does not exist");
        }
        self.totalForms( self.totalForms() + 1 );
        ko.applyBindings(this, div.get()[0]);
    };
}
