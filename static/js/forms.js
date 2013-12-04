
function addChildForm(inputDom, form, target){
    console.log("Adding form of type: ", form);
    dust.render(form, {}, function(err, out){
        if(err){
            console.log(err);
        }
        target = target || $(inputDom).parent();
        target.append($(out));
        // TODO: Update the management form
        
    }); 
}