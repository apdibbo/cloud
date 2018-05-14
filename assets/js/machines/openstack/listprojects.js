function getProjects() {
    $.ajax({
        type: "GET",
        url: "/api/projects",
        statusCode: {
            500: function() {
                   $("#errormessage").html("The cloud may be experiencing problems. Please try again later.");
                   $("#error").show();
            }
        }
    }).done(function(data) {
        if (!(data['data'].length >= 1)) {
              $("#errormessage").html("You do not have access to any projects");
              $("#error").show();
        } else {
              $('#loading-project').hide();
              var projectList = data;
              var select = document.getElementById("projectChoice");
              for (i = 0; i < projectList['data'].length; i++){
                  select.options[select.options.length] = new Option(projectList['data'][i]['name'], projectList['data'][i]['id']);
              }
        
              var selItem = Cookies.get("projectID");
              for (i = 0; i < Object.values(data.data).length; i++){
                  if (Object.values(data.data[i]).includes(selItem)) {
	              $('#projectChoice').val(selItem);
	          }
              }

              makeAjaxCalls();
        }
    });
}

var loadedProject = {};

function makeAjaxCalls() {

    loadedProject = {
        'quota'     : false,
        'templates' : false,
        'flavors'   : false,
        'vms'       : false,
        'vnc'       : false
    };

    $('.quotaBox').hide();
    loadingWheels();

    var date = new Date();
    date.setTime(date.getTime() + (86400 * 1000));    // Cookie will expire 24 hours after creating
    Cookies.set("projectID", document.getElementById("projectChoice").value, {expires : date, path : '/'});
 
    getTemplateList();
    getFlavors();
    quota.update();
    drawTable(miscAction);
    addVNC();
}

function loadingWheels() {

    if (loadedProject['quota'] == true && loadedProject['templates'] == true && loadedProject['flavors'] == true) {
        $('#newMachine').removeAttr('disabled');
    } else {
        $('#newMachine').attr('disabled', '');
    }

    for (wheel in loadedProject) {
        if (loadedProject[wheel] == true ) {
            console.log("hide " + wheel);
            $('#loading-' + wheel).hide();
            $('#loading-' + wheel + '-big').hide();
        } else {
            $('#loading-' + wheel).show();
            $('#loading-' + wheel + '-big').show();
        }
    }

    if (Object.values(loadedProject).includes(false) === false) {
        $('#loading-all').hide();
    } else {
        $('#loading-all').show();
    }

}
