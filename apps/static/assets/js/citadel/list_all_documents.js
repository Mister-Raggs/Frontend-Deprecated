$(function () {
    // Function to toggle the right sidebar
    function toggleRightSidebar() {
        $('body').toggleClass('control-sidebar-open');
    }
    // util function to get row id from tr row
    function get_dt_row_id($button, $dataTable) {
        tr = $button.closest('tr');
        row = $dataTable.row(tr);
        data = row.data()
        if (!data) {
            // main row is possibly collapsed so try parent approach
            tr = tr.prev();
            row = $dataTable.row(tr);
            data = row.data()
        }
        return data.DT_RowId;
    }
    // util function to get row id from tr row
    function get_document_name($button, $dataTable) {
        tr = $button.closest('tr');
        row = $dataTable.row(tr);
        data = row.data()
        if (!data) {
            // main row is possibly collapsed so try parent approach
            tr = tr.prev();
            row = $dataTable.row(tr);
            data = row.data()
        }
        return data.document_name;
    }
    function handle_preview_document_action($button, $dataTable) {
        // Get the row ID and document name from the DataTable
        var row_id = get_dt_row_id($button, $dataTable);
        var document_name = get_document_name($button, $dataTable);

        // Log the Preview action    
        console.log("Preview action triggered for row id: " + row_id);
        window.open('/citadel/api/document_preview?document_id=' + row_id, '_blank')

    }
    function handleDownloadButtonClick(rowId, action, documentName) {
        console.log("Download triggered for document id: " + rowId);
    
        // Send a POST request to the server to initiate the download
        $.ajax({
            url: "/citadel/api/download_document",
            method: "POST",
            data: {
                document_id: rowId, // Use rowId parameter
                action: action,     // Use action parameter
            },
            xhrFields: {
                responseType: "blob",
            },
            success: function (data, status, xhr) {
                // Once the POST request is successful, initiate the download
                var blobData = data; // The response data is already a Blob
                var blobUrl = window.URL.createObjectURL(blobData);
                // Create a popup window with the download prompt
                var a = document.createElement('a');
                a.style.display = 'none';
                a.href = blobUrl;
                a.setAttribute('download', documentName); // Use the provided documentName
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(blobUrl);
                document.body.removeChild(a);
            },
            error: function (xhr, status, error) {
                show_toast_notification("error", "Error!", "Download failed for document '" + documentName + "'.<br />Error from server is: " + xhr.statusText);
            },
        });
    }
    function handle_activate_delete_toggle_button_action($button, $dataTable, $action) {
        row_id = get_dt_row_id($button, $dataTable)
        document_name = get_document_name($button, $dataTable)
        console.log("Toggle action '" + $action + "', triggered for row id: " + row_id)
        if ($action == "")
            $action_name
        $.post("/citadel/api/document_toggle_activate_delete",
            {
                document_id: row_id,
                action: $action,
            }).done(function (result, status, xhr) {
                $dataTable.ajax.reload(null, false)
                console.log("Toggle action '" + $action + "', completed for row id: " + row_id + " and table updated.")
                show_toast_notification("success", "Success!", "Toggle action '" + $action +
                    "', completed for document'" + document_name + "'' and table updated.")
            }).fail(function (xhr, status, error) {
                show_toast_notification("error", "Error!", "Toggle action '" + $action +
                    "', failed for document '" + document_name + "''. <br />Error from server is: " + xhr.statusText)
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
    $dtable = $('#documents_list_table').DataTable({
        serverSide: true,
        processing: true,
        stateSave: true,
        'serverMethod': 'post',
        'ajax': {
            'url': '/citadel/api/get_list_document_data'
        },
        'columns': [
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
                    $is_active = data.is_active
                    $button_group = '<div class="btn-group">' +
                        '       <button type="button" id="row-preview-button" class="btn btn-info btn-sm" ' +
                        '               data-toggle="tooltip" title="Click to \'Preview\' this document.">' +
                        '           <i class="fa fa-eye"></i>' +
                        '       </button>' +
                        '       &nbsp;&nbsp;'
                    // activate or deactivate button
                    if ($is_active.toUpperCase() == "YES") {
                        $button_group += '       <button type="button" id="is-active-toggle-button" class="btn btn-warning btn-sm" ' +
                            '                               data-toggle="tooltip" title="Click to \'De-Activate\' this document." >' +
                            '                       <i class="fas fa-toggle-on fa-lg"></i>'
                    } else {
                        $button_group += '       <button type="button" id="is-active-toggle-button" class="btn btn-warning btn-sm" ' +
                            '                               data-toggle="tooltip" title="Click to \'Activate\' this document." >' +
                            '                       <i class="fas fa-toggle-off fa-lg"></i>'
                    }

                    $button_group += '      </button>'
                    $button_group += '       &nbsp;&nbsp;'

                    // latest status button
                    $button_group += '       <button type="button" id="latest-status-button" class="btn btn-primary btn-sm" ' +
                        '               data-toggle="tooltip" title="Click to view the \'Status\' of this document.">' +
                        '           <i class="fa fa-info-circle"></i>' +
                        '       </button>' +
                        '       &nbsp;&nbsp;'
                    $button_group += '   </button>'

                    //download button
                    $button_group += '<button type="button" id="download-button" class="btn btn-primary btn-sm" data-toggle="tooltip" title="Click to download this document">' +
                        '<i class="fa fa-download"></i>' +
                        '</button>&nbsp;&nbsp;' +
                        '</div>';
                    $button_group += '   </button>'
                    return $button_group;

                },
            },

        ],
        'lengthMenu': [
            [10, 20, 30, 50, 75],
            [10, 20, 30, 50, 75]
        ],
        'searching': true,
        'sort': false,
        'info': true,
        'autoWidth': false,
        'responsive': true,
        "drawCallback": function (settings) {

            //toggle tooltips for action buttons
            $('#documents_list_table [data-toggle="tooltip"]').tooltip();
        },
    });
    // Logic to enable type ahead search after alteast 3 characters or
    // if the user hits enter
    $(".dataTables_filter input")
        .unbind() // Unbind previous default bindings
        .bind("input", function (e) { // Bind our desired behavior
            // If the length is 3 or more characters, or the user pressed ENTER, search
            if (this.value.length >= 3 || e.keyCode == 13) {
                // Call the API search function
                $dtable.search(this.value).draw();
            }
            // Ensure we clear the search if they backspace far enough
            if (this.value == "") {
                $dtable.search("").draw();
            }
            return;

        });
    // handle the activate/deactivate button click
    $('#documents_list_table tbody').on('click', 'button#is-active-toggle-button', function () {
        handle_activate_delete_toggle_button_action($(this), $dtable, "is_active",)
    });

    //handle document preview button click
    $('#documents_list_table tbody').on('click', 'button#row-preview-button', function () {
        handle_preview_document_action($(this), $dtable, "document_name",)
    });

    // handle download button
    $('#documents_list_table tbody').on('click', 'button#download-button', function () {
        var rowId = get_dt_row_id($(this), $dtable);
        var documentName = get_document_name($(this), $dtable);
        var action = 'download'; // Assuming the action is 'download', adjust as necessary
        handleDownloadButtonClick(rowId, action, documentName);
    });

    // enable tooltips on action buttons
    $('[data-toggle="tooltip"]').tooltip();

    $('.toastsDefaultAutohide').click(function () {
        $(document).Toasts('create', {
            title: 'Toast Title',
            class: 'bg-success',
            autohide: true,
            delay: 1000,
            body: 'Lorem ipsum dolor sit amet, consetetur sadipscing elitr.'
        })
    });

    // Event handler for the right sidebar toggle button
    $('#rightSidebarToggle').on('click', function (e) {
        e.preventDefault();
        toggleRightSidebar();
    });

    // Close the right sidebar when clicking outside of it
    $(".content-wrapper").on('click', function (e) {
        if (
            $(e.target).closest('.control-sidebar').length === 0 &&
            !$(e.target).is('#rightSidebarToggle')
        ) {
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