// Function for get ajax response for check username availability
(function() {
    window.addEventListener('load', function() {
        var username = document.getElementById('username');
        var forms = document.getElementsByClassName('cuser');
        var validation = Array.prototype.filter.call(forms, function(form) {
            form.addEventListener('submit', function(event) {
                event.preventDefault();
                $.get("/check?username=" + username.value, function(data) {
                    if (data == false) {
                        $("#myModal").on("show", function() {
                            $("#myModal a.btn").on("click", function(e) {
                                console.log("button pressed");
                                $("#myModal").modal('hide');
                            });
                        });

                        $("#myModal").on("hide", function() {
                            $("#myModal a.btn").off("click");
                        });

                        $("#myModal").on("hidden", function() {
                            $("#myModal").remove();
                        });

                        $("#myModal").modal({
                            "backdrop": "static",
                            "keyboard": true,
                        });
                    } else if (data == true) {
                        form.submit();
                    }
                });
            });
        });
    });
})();

// Example starter JavaScript for disabling form submissions if there are invalid fields
(function() {
    'use strict';
    window.addEventListener('load', function() {
        // Fetch all the forms we want to apply custom Bootstrap validation styles to
        var forms = document.getElementsByClassName('needs-validation');
        // Loop over them and prevent submission
        var validation = Array.prototype.filter.call(forms, function(form) {
            form.addEventListener('submit', function(event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();


// validtion for password match
var check = function() {
    // if passwords are match print matching
    if (document.getElementById('password').value ==
        document.getElementById('confirmation').value) {
        document.getElementById('message').style.color = '#28a745';
        document.getElementById('message').innerHTML = 'matching';
        // if passwords are not match print not matching
    } else {
        document.getElementById('message').style.color = '#dc3545';
        document.getElementById('message').innerHTML = 'not matching';
    }
}

// function for setting username and password page
function myform(name) {
    if (name == "")
        return;

    var ajax = new XMLHttpRequest();

    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200) {
            $('#settingform').html(ajax.responseText);
        }
    };
    ajax.open('GET', '/static/' + name + '.html', true);
    ajax.send();

    return false;
}