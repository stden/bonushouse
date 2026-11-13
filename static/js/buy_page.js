$(function(){
//Страница покупки купона
    $('.quantity input').numeric({ decimal: false, negative: false });
    $('.quantity .minus').click(function(){
        quantity = $('input', $(this).parents('.quantity:first')).val();
        quantity = parseInt(quantity);
        if(quantity>1) {
            $('input', $(this).parents('.quantity:first')).val(quantity-1).change();
        }
        return false;
    });
    $('.quantity .plus').click(function(){
        quantity = $('input', $(this).parents('.quantity:first')).val();
        quantity = parseInt(quantity);
        $('input', $(this).parents('.quantity:first')).val(quantity+1).change();
        return false;
    });
//Обновление количества купонов. Пересчет цены.
    $('.quantity input').change(function(){
        quantity = parseInt($('.quantity input', $(this).parents('form:first')).val());
        price_money = parseFloat($('input[name=price_money]',$(this).parents('form:first')).val());
        price_bonuses = parseFloat($('input[name=price_bonuses]',$(this).parents('form:first')).val());
        temp_price_money = price_money*quantity;
        temp_price_bonuses = price_bonuses*quantity;
        money_ballance = parseInt($('input[name=money_ballance]', $(this).parents('form:first')).val());
        bonuses_ballance = parseInt($('input[name=bonuses_ballance]', $(this).parents('form:first')).val());
        $('input[name=temp_price_money]', $(this).parents('form:first')).val(temp_price_money);
        $('input[name=temp_price_bonuses]', $(this).parents('form:first')).val(temp_price_bonuses);
        $('.offer_info .price .money', $(this).parents('form:first')).text(temp_price_money+' р.');
        $('.offer_info .price .bonuses', $(this).parents('form:first')).text(temp_price_bonuses+' бонусов');
        if(money_ballance<temp_price_money) {
            $('#payment_deposit .not_enough').text('Недостаточно денег на счету для оплаты заказа');
            $('#payment_deposit .pay').addClass('disabled');
        }
        else {
            $('#payment_deposit .not_enough').text('');
            $('#payment_deposit .pay').removeClass('disabled');
        }
        if(bonuses_ballance<temp_price_bonuses) {
            $('#payment_bonuses .not_enough').text('Недостаточно бонусов на счету для оплаты заказа');
            $('#payment_bonuses .pay').addClass('disabled');
        }
        else {
            $('#payment_bonuses .not_enough').text('');
            $('#payment_bonuses .pay').removeClass('disabled');
        }
    });
    $('.payment_switch li a').click(function() {
        $('.tab', $(this).parents('form:first')).hide();
        $($(this).attr('href')).show();
        $('.payment_switch li a').removeClass('current');
        $(this).addClass('current');
        return false;
    });
    $('.payment_switch li a:first').click();
    $('#payment_deposit .pay').click(function() {
        if(!$(this).hasClass('disabled')) {
            $('#id_payment_type').val(1);
            $('#buy_offer_form').submit();
        }
        return false;
    });
    $('#payment_bonuses .pay').click(function() {
        if(!$(this).hasClass('disabled')) {
            $('#id_payment_type').val(2);
            $('#buy_offer_form').submit();
        }
        return false;
    });
    $('#payment_others .pay').click(function() {
        if(!$(this).hasClass('disabled')) {
            $('#id_payment_type').val(3);
            $('#buy_offer_form').submit();
        }
        return false;
    });
    $('.quantity input').change();
});