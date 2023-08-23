$(function () {

    // disable password and confirm password required validation rules for update form only.
    // its possible that user's other details need ot be updated only and nothing else.
    // but if password or confirm password is updated then their equalsTo rule still applies
    function disable_password_fields_required_validation() {
        $form_type = $("#form_type")
        $row_id = $("#row_id")
        if (($form_type.val().toUpperCase() == "update".toUpperCase()) && $row_id.val()) {
            return false
        } else {
            return true
        }
    }

    //Initialize Select2 Elements
    $('.select2bs4').select2({
        theme: 'bootstrap4'
    })

    $("#show_hide_password a").on('click', function (event) {
        event.preventDefault();
        if ($('#show_hide_password input').attr("type") == "text") {
            $('#show_hide_password input').attr('type', 'password');
            $('#show_hide_password i').addClass("fa-eye-slash");
            $('#show_hide_password i').removeClass("fa-eye");
        } else if ($('#show_hide_password input').attr("type") == "password") {
            $('#show_hide_password input').attr('type', 'text');
            $('#show_hide_password i').removeClass("fa-eye-slash");
            $('#show_hide_password i').addClass("fa-eye");
        }
    });

    $("#show_hide_confirm_password a").on('click', function (event) {
        event.preventDefault();
        if ($('#show_hide_confirm_password input').attr("type") == "text") {
            $('#show_hide_confirm_password input').attr('type', 'password');
            $('#show_hide_confirm_password i').addClass("fa-eye-slash");
            $('#show_hide_confirm_password i').removeClass("fa-eye");
        } else if ($('#show_hide_confirm_password input').attr("type") == "password") {
            $('#show_hide_confirm_password input').attr('type', 'text');
            $('#show_hide_confirm_password i').removeClass("fa-eye-slash");
            $('#show_hide_confirm_password i').addClass("fa-eye");
        }
    });

    $("#reset-button").click(function () {

    });

    // Adding check for default value on select options
    jQuery.validator.addMethod("notEqual", function (value, element, param) {
        return this.optional(element) || value !== param;
    }, "Please choose a value!");

    //validation rules from here
    $form_type = $("#form_type").val
    $row_id = $("#row_id")
    $pass = $('#password')
    $confirm_pass = $('#confirm_password')

    var $validator = $('#add-update-user-form').validate({
        submitHandler: function (form) {
            form.submit();
        },
        rules: {
            salutation: {
                required: true,
            },
            first_name: {
                required: true,
            },
            last_name: {
                required: true,
            },
            email: {
                required: true,
                email: true,
            },
            company: {
                required: true,
                notEqual: "-1",
            },
            password: {
                required: disable_password_fields_required_validation(),
                minlength: 8,
            },
            confirm_password: {
                required: disable_password_fields_required_validation(),
                equalTo: "#password",
            },
            user_type: {
                required: true,
                notEqual: "-1",
            },
            role: {
                required: true,
                notEqual: "-1",
            },
        },
        messages: {
            salutation: {
                required: "Please choose user salutation."
            },
            first_name: {
                required: "Please provide user first name."
            },
            last_name: {
                required: "Please provide user last name."
            },
            email: {
                required: "Please enter the user's email address.",
                email: "Please provide a valid email address.",
            },
            company: {
                required: "Please choose the user's company.",
                notEqual: "Please choose the user's company."
            },
            password: {
                required: "Please enter the password.",
                minlength: "Password of minimum of 8 characters length is required."
            },
            confirm_password: {
                equalTo: "Password and Confirm Password don't match.",
            },
            user_type: {
                required: "Please choose the user type.",
                notEqual: "Please choose the user type."
            },
            role: {
                required: "Please choose the user's role.",
                notEqual: "Please choose the user's role'."
            }
        },
        errorElement: 'span',
        errorPlacement: function (error, element) {
            error.addClass('invalid-feedback');
            element.closest('.form-group').append(error);
        },
        highlight: function (element, errorClass, validClass) {
            $(element).addClass('is-invalid');
        },
        unhighlight: function (element, errorClass, validClass) {
            $(element).removeClass('is-invalid');
        }
    });

});