
function addChildForm(inputDom, form, formPrefix){
    console.log("Adding form of type: ", form);
    // Figure out what index this needs to be...
    // Use the count as the current Id then increment it...
    var sel = "#id_" + formPrefix + "-TOTAL_FORMS";
    console.log("Selector: ", sel);
    var count = parseInt($(sel).val());
    $(sel).val(count + 1);

    console.log("The index is now: " + count);

    dust.render(form, {"index" : count}, function(err, out){
        if(err){
            console.log(err);
        }
        var target = $(inputDom).parent();
        target.append($(out));

    }); 
}