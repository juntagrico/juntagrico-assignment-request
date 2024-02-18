$( document ).ready(function() {
    let areas = JSON.parse(document.getElementById('approvers_data').textContent)
    let area_select = $('select#id_activityarea')
    area_select.on('change', function() {
        filter_approvers(areas, this.value)
    })
    filter_approvers(areas, area_select.val())
});

function filter_approvers(areas, selected_area) {
    // reduce visible options of approvers based on selected area
    let approver_select = $('select#id_approver')
    approver_select.find('option').show()
    for (const [area, approver] of Object.entries(areas)) {
        let show = area === selected_area
        approver_select.find('option[value=' + approver + ']').toggle(show)
        // disselect approver if option is hidden
        if (!show && String(approver) === approver_select.val()) {
            approver_select.val('').change()
        }
    }
}
