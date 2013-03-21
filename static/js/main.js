$(document).ready(function(){
    //Аттрибут placecholder Для ие
    $("input[placeholder], textarea[placeholder]").placeholder();
    //Слайдер
    $('#slideshow').cycle({
        fx: 'fade',
        speed:2000,
        prev:'#prev',
        next:'#next',
        timeout:3000
    });
    //Голосование в отзывах
    $('input.star-rating').rating();
    $('.countdown').each(function() {
        countDown($(this));
    });
    //Поля ввода
    $(".mask_phone").mask("8(999)9999999");
    $(".mask_date").mask("99.99.9999");
    //Ссылка "Позвоните мне"
    $('#call_me_link').click(function() {
        $.blockUI({
            message: $('#call_me_overlay'),
            css:{width:'760px',
                background:'none',
                border:'none',
                left:'35%',
                top:'10%',
                textAlign:'left',
                cursor:'default'
            }
        });
        $('.blockOverlay').attr('title','Щелкните, чтобы закрыть').click($.unblockUI);
    });
    $('.call_me_overlay_close').click(function() {
        $.unblockUI();
        return false;
    });
    $('.share_link_email').click(function() {
        $.blockUI({
            message: $('#share_link_overlay'),
            css:{width:'760px',
                background:'none',
                border:'none',
                left:'30%',
                top:'10%',
                textAlign:'left',
                cursor:'default'
            }
        });
        $('.blockOverlay').attr('title','Щелкните, чтобы закрыть').click($.unblockUI);
        return false;
    });
    $('#share_link_email_form').live('submit', function() {
        $.post('/share-link/', $(this).serialize(), function(data){
            $('.blockUI #share_link_email_form .ajax_messages').html(data.message);
            if(data.success) {
                $('.blockUI #share_link_email_form .form_row').detach();
                $('.blockUI #share_link_email_form .close_row').show();
            }
        },'json');
        return false;
    });
    //Предупреждения
    $('.warning_message_overlay .agreed_link').click(function() {
        return checkWarningAgree($(this));
    });
    showWarningAgree();
    //Подарить
    $('.cart-gift-buttons .gift').click(function() {
        $.get($(this).attr('href'), {}, function(data){
            if(data.success) {
                $.blockUI(
                    {
                        message: data.message,
                        css: {
                            borderRadius: '10px',
                            fontSize: '30px',
                            padding: '20px',
                            lineHeight: '1.4'
                        }
                    }
                );
                $('.header-area .cart-count').text(data.newCartCount);
                $('.blockOverlay').attr('title','Щелкните, чтобы закрыть').click($.unblockUI);
            }
        },'json');
        return false;
    });
});
function showWarningAgree() {
    if($('.warning_need_agree').length) {
        $.blockUI({
            message: $('.warning_need_agree:first'),
            css:{width:'760px',
                background:'none',
                border:'none',
                left:'30%',
                top:'10%',
                textAlign:'left',
                cursor:'default'
            }
        });
        $('.blockOverlay').removeAttt('title').click(function() {return false});
    }
}
function checkWarningAgree(sender) {
    if($('input:checkbox:checked', sender.parents('.warning_message_overlay:first')).length) {
        $.unblockUI();
        sender.parents('.warning_message_overlay:first').removeClass('warning_need_agree');
        showWarningAgree();
    }
    else {
        alert('Пожалуйста, подтвердите, что вы ознакомлены с предупреждением');
    }
    return false;
}