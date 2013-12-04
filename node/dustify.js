// Adopted from https://github.com/dmix/dusterjs/blob/master/duster.js


var folder = __dirname + "/../form_templates"
if(folder.charAt(folder.length-1) == "/"){
  folder = folder.substring(0, folder.length-1);
}

/**
 * The file extension the watch module should look for to recompile files
 * @property {String}
 */
var fileExt = ".form";

var templateJs = folder + "/../static/js/templates.js";
var templateData = {};

var fs = require('fs');
var dust = require('dustjs-linkedin');
var watch = require('watch');

function recompileTemplate(file){
  var fileName = folder + "/" + file;
  fs.readFile(fileName, function(err,data){
    if (err) throw err; 
      var templateName = file.split(fileExt)[0];
      console.log("[DUST] Recompiling " + templateName + " for " + fileName);
      try {
        var compiled = dust.compile(new String(data), templateName);
        templateData[templateName] = compiled;
      } catch(e){
        console.log("[DUST] ERROR occurred while trying to compile " + templateName + "\n" + e);
        console.log("[DUST] Template contents: " + new String(data));
      }
      updateTemplateJs();
    });
}

function updateTemplateJs(){
  var contents = "";
  for(template in templateData){
    contents += templateData[template];
  }
  fs.writeFile(templateJs, contents, function(err){
    if(err){
      console.log("[DUST] Error writing templates file! " + err);
    }
  });
}

function recompileTemplates(path, curr, prev) {
  dust = require('dustjs-linkedin'); // reset dust
  fs.readdir(folder, function(err, files){
    console.log("[DUST] " + files.length + " files to recompile");
    for(var i = 0; i < files.length; i++){
      var file = files[i];
      if(file.indexOf(fileExt) > -1 && file.indexOf("#") == -1){
        recompileTemplate(file);
      } else {
        //console.log("[DUST] Skipping " + file);
      }
    }
  });
}

watch.createMonitor(folder, function (monitor) {
  console.log("[DUST] Watching " + folder + " to update " + templateJs);
  monitor.files["*" + fileExt, '*/*'];
  monitor.on("created", recompileTemplates);
  monitor.on("changed", recompileTemplates);
});

// Recompile the templates
recompileTemplates();