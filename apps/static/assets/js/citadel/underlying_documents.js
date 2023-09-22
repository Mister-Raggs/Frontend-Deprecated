$(function () {
    // Function to toggle the right sidebar
    function toggleRightSidebar() {
        $('body').toggleClass('control-sidebar-open');
    }

    // Util function to get row id from tr row
    function get_dt_row_id($button, $dataTable) {
        tr = $button.closest('tr');
        row = $dataTable.row(tr);
        data = row.data();
        if (!data) {
            // Main row is possibly collapsed so try parent approach
            tr = tr.prev();
            row = $dataTable.row(tr);
            data = row.data();
        }
        return data.DT_RowId;
    }

    // Util function to get document name from tr row
    function get_document_name($button, $dataTable) {
        tr = $button.closest('tr');
        row = $dataTable.row(tr);
        data = row.data();
        if (!data) {
            // Main row is possibly collapsed so try parent approach
            tr = tr.prev();
            row = $dataTable.row(tr);
            data = row.data();
        }
        return data.document_name;
    }

    function handle_actions($button, $dataTable, $action) {
        row_id = get_dt_row_id($button, $dataTable);
        document_name = get_document_name($button, $dataTable);
        $.post("/citadel/api/underlying_document_actions", {
            document_id: row_id,
            action: $action,
        });
    }
    function show_toast_notification(toast_type, title, msg) {
        toast_class = ""
        if (toast_type == "success") {
            toast_class = "bg-success"
        } else if (toast_type == "error") {
            toast_class = "bg-warning"
        } else {
            toast_class = "bg-info"
        }
        $(document).Toasts('create', {
            title: title,
            class: toast_class,
            autohide: true,
            delay: 2100,
            body: msg,
        })
    }
    $dtable = $('#underlying_documents_list_table').DataTable({
        serverSide: true,
        processing: true,
        stateSave: true,
        serverMethod: 'post',
        ajax: {
            url: '/citadel/api/get_list_underlying_data',
        },
        columns: [
            { data: 'document_name', searchable: true },
            { data: 'uploaded_by', searchable: true },
            { data: 'document_type_size' },
            { data: 'created_date' },
            { data: 'last_modified_date' },
            { data: 'latest_status' },
            { data: 'is_active' },
            {
                data: null,
                render: function (data, type, row, meta) {
                    // Preview and Download buttons
                    return '<div class="btn-group">' +
                        '<button type="button" id="row-preview-button" class="btn btn-info btn-sm" data-toggle="tooltip" title="Click to \'Preview\' this document.">' +
                        '<i class="fa fa-eye"></i>' +
                        '</button>&nbsp;&nbsp;' +
                        '<button type="button" id="download-button" class="btn btn-primary btn-sm" data-toggle="tooltip" title="Click to download this document">' +
                        '<i class="fa fa-download"></i>' +
                        '</button>&nbsp;&nbsp;' +
                        '</div>';
                },
            },
        ],
        lengthMenu: [
            [10, 20, 30, 50, 75],
            [10, 20, 30, 50, 75],
        ],
        searching: true,
        sort: false,
        info: true,
        autoWidth: false,
        responsive: true,
        drawCallback: function (settings) {
            // Toggle tooltips for action buttons
            $('#underlying_documents_list_table [data-toggle="tooltip"]').tooltip();
        },
    });

    // Logic to enable type ahead search after at least 3 characters or if the user hits enter
    $(".dataTables_filter input")
        .unbind() // Unbind previous default bindings
        .bind("input", function (e) { // Bind our desired behavior
            if (this.value.length >= 3 || e.keyCode == 13) {
                // Call the API search function
                $dtable.search(this.value).draw();
            }
            // Ensure we clear the search if they backspace far enough
            if (this.value == "") {
                $dtable.search("").draw();
            }
        });

    // Enable tooltips on action buttons
    $('[data-toggle="tooltip"]').tooltip();
    $('.toastsDefaultAutohide').click(function () {
        $(document).Toasts('create', {
            title: 'Toast Title',
            class: 'bg-success',
            autohide: true,
            delay: 1000,
            body: 'Lorem ipsum dolor sit amet, consetetur sadipscing elitr.',
        });
    });

    // Event handler for the right sidebar toggle button
    $('#rightSidebarToggle').on('click', function (e) {
        e.preventDefault();
        toggleRightSidebar();
    });

    // Close the right sidebar when clicking outside of it
    $(".content-wrapper").on('click', function (e) {
        if ($(e.target).closest('.control-sidebar').length === 0 && !$(e.target).is('#rightSidebarToggle')) {
            if ($('body').hasClass('control-sidebar-open')) {
                toggleRightSidebar();
            }
        }
    });

    $('#clear_state').on('click', function (e) {
        $dtable.state.clear();
        window.location.reload();
    });
});
