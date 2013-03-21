$(function() {
    $('#bulk-actions-select').change(function() {
        if($(this).val()!='') {
            if($(this).val()!='delete' || confirm('Удалить выбранные записи? Вы уверены?')) {
                $('#bulk_action_form input[name=action]').val($(this).val());
                $('#bulk_action_form').submit();
            }
        }
    });
    $('#bulk_action_form #check-all').bind('change.crc', function() {

        if($(this).is(':checked')) {
            $('.check-bulk').each(function(){
                $(this).attr('checked', 'checked').trigger('change.crc')
            });
        }
        else {
            $('.check-bulk').each(function(){ $(this).removeAttr('checked').trigger('change.crc')});
        }
    });
    $('.datepicker').datepicker();
    $('.datetimepicker').datetimepicker();
});