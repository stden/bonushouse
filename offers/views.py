# -*- coding: utf-8 -*-
from offers.models import Offers, Order, AbonementOrder, AdditionalServicesOrder, GiftOrder
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from offers.forms import BuyOfferForm, AbonementsAdditionalInfoForm, SimpleActionAdditionalInfoForm, AbonementsClubCardForm, GiftOfferForm, get_clubs_by_card_number
from payment_gateways.models import PaymentRequest
from bonushouse.forms import FeedbacksForm
from bonushouse.models import UserRatings, UserFeedbacks
from django.contrib import messages
from offers.utils import update_last_viewed_offers
from django.http import Http404, HttpResponse
from offers.cart import ShoppingCart
from dbsettings.models import Settings
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse_lazy
from likes.functions import get_likes_count, toggle_like
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils import timezone
import datetime


def view(request, offer_id):
    offer_id = int(offer_id)
    offer = get_object_or_404(Offers.all_objects, pk=offer_id)
    context = RequestContext(request)
    if offer.partner.admin_user == request.user:
        can_write_replies = True
    else:
        can_write_replies = False
    context['can_write_replies'] = can_write_replies
    context['offer'] = offer
    if request.method == 'POST':
        feedback_form = FeedbacksForm(request.POST)
        if (request.user.is_staff or can_write_replies) and request.POST.get('admin-reply'):
            admin_reply = request.POST.get('admin_reply')
            feedback_id = request.POST.get('feedback_id')
            if feedback_id:
                try:
                    feedback_id = int(feedback_id)
                    feedback = UserFeedbacks.objects.get(pk=feedback_id)
                    if not request.user.is_staff and feedback.content_object.partner.admin_user != request.user:
                        raise Http404
                    feedback.admin_reply = admin_reply
                    feedback.save()
                    return redirect(offer.get_url())
                except:
                    pass
        else:
            if feedback_form.is_valid():
                feedback_form.instance.content_object = offer
                feedback_form.instance.user = request.user
                feedback_form.save()
                rating = UserRatings(content_object=feedback_form.instance, user=request.user, rating=feedback_form.cleaned_data['rating'])
                rating.save()
                messages.info(request, 'Спасибо! Ваш отзыв отправлен на проверку администрации.')
                return redirect(offer.get_url())
    else:
        feedback_form = FeedbacksForm()
    context['feedback_form'] = feedback_form
    update_last_viewed_offers(request, offer)
    offer.views_count += 1
    offer.save()
    if offer.get_seo_meta_object():
        seo_meta = offer.get_seo_meta_object()
        context['META_TITLE'] = seo_meta.meta_title
        context['META_KEYWORDS'] = seo_meta.meta_keywords
        context['META_DESCRIPTION'] = seo_meta.meta_description
    return render_to_response('offers/view.html', context)


def cart_add(request, offer_id):
    offer = get_object_or_404(Offers.all_objects, pk=offer_id)
    cart = ShoppingCart(request)
    is_success = False
    is_gift = request.GET.get('is_gift')
    if is_gift == '1':
        if request.is_ajax():
            cart_item_id = cart.add_item(request, offer, is_gift=True, force_new_item=True)
            if cart_item_id:
                result = {
                    'success': True,
                    'message': 'Подарок в вашей корзине. <a href="%s">Оплатить</a>/<a href="#" onclick="$.unblockUI(); return false;">продолжить покупки</a>' % (reverse_lazy('offers.views.cart_buy', kwargs={'item_id':cart_item_id}),),
                    'newCartCount': len(cart.get_contents()),
                    }
            else:
                result = {
                    'success': True,
                    'message': 'Купоны по этой акции закончились. Их больше нельзя купить.',
                    'newCartCount': len(cart.get_contents()),
                    }
            return HttpResponse(simplejson.dumps(result))
        else:
            return redirect(offer.get_url())
    elif offer.is_abonement() or offer.is_additional_service():
        context = RequestContext(request)
        context['offer'] = offer
        # Возвращает None, если кол-во купонов = 0
        is_success = cart.add_item(request, offer, force_new_item=True)
        if is_success:
            messages.info(request, ('Акция добавлена в вашу <a href="%s">корзину</a>' % (reverse_lazy('offers.views.cart'))))
        return redirect(offer.get_url())
    else:
        is_success = cart.add_item(request, offer)
        if is_success:
            messages.info(request, ('Акция добавлена в вашу <a href="%s">корзину</a>' % (reverse_lazy('offers.views.cart'))))
        return redirect(offer.get_url())


@login_required
def buy(request, offer_id):
    offer_id = int(offer_id)
    offer = get_object_or_404(Offers, pk=offer_id)
    return buy_view(request, offer)


def cart(request):
    context = RequestContext(request)
    cart = ShoppingCart(request)
    context['cart'] = cart
    return render_to_response('users/cart.html', context)


def cart_clear(request):
    cart = ShoppingCart(request)
    cart.clear()
    return redirect('cart')


@login_required
def cart_buy(request, item_id):
    cart = ShoppingCart(request)
    item = cart.get_item(item_id)
    if not item:
        raise Http404
    offer = item['item']
    return buy_view(request, offer, item)


def buy_view(request, offer, cart_item=None):
    context = RequestContext(request)
    if not offer.can_buy():
        messages.info(request, 'К сожалению, купоны по данной акции закончились')
        return redirect(offer.get_url())
    context['offer'] = offer
    if cart_item is not None:
        cart = ShoppingCart(request)
        context['is_cart_item'] = True
    if cart_item is not None and cart_item['is_gift']:
        #Мы имеем дело с подарком
        return buy_gift_view(request, offer, cart_item)
    elif offer.is_abonement():
        #Мы имеем дело с абонементом
        if request.method == 'POST':
            additional_info_form = AbonementsAdditionalInfoForm(request.POST, offer=offer)
            buy_form = BuyOfferForm(request.POST, user=request.user, offer=offer, initial={'quantity':1})
            if additional_info_form.is_valid() and buy_form.is_valid():
                additional_info_form.save()
                abonement_order = AbonementOrder(offer=offer, user=request.user, visitor_info=request.session['visitor_info'], additional_info=additional_info_form.instance)
                if buy_form.cleaned_data['payment_type'] == 1:
                    #Если выбрали оплату с депозита, сразу списываем деньги и завершаем заказ
                    abonement_order.price = offer.coupon_price_money
                    abonement_order.price_type = 1
                    abonement_order.save()
                    profile = request.user.get_profile()
                    transaction = profile.withdraw_money_deposit(abonement_order.price, u"Оплата заказа %s (%s)" % (abonement_order.pk, offer.title,))
                    abonement_order.complete(transaction)
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return redirect('cabinet_abonements')
                elif buy_form.cleaned_data['payment_type'] == 2:
                    #Аналогично с оплатой бонусами
                    abonement_order.price = offer.coupon_price_bonuses
                    abonement_order.price_type = 2
                    abonement_order.save()
                    profile = request.user.get_profile()
                    transaction = profile.withdraw_bonuses(abonement_order.price, u"Оплата заказа %s (%s)" % (abonement_order.pk, offer.title,))
                    abonement_order.complete(transaction)
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return redirect('cabinet_abonements')
                elif buy_form.cleaned_data['payment_type'] == 3:
                    abonement_order.price = offer.coupon_price_money
                    abonement_order.price_type = 1
                    abonement_order.save()
                    payment_request = PaymentRequest(inner_transaction=abonement_order, amount=abonement_order.price, comment=u"Bonus-House.ru. Оплата заказа #%s. Пользователь #%s" % (abonement_order.pk, abonement_order.user.pk,))
                    payment_request.save()
                    context = RequestContext(request)
                    context['amount'] = abonement_order.price
                    context['nickname'] = request.user.email
                    context['order_id'] = payment_request.pk
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return render_to_response('payments/dol/redirect_form.html', context)
        else:
            if cart_item is not None:
                initial = cart_item['additional_info']
            else:
                initial = None
            initial = {'first_name': request.user.first_name,
                       'last_name': request.user.last_name,
                       'email': request.user.email,
                       'birth_date': request.user.get_profile().birth_date,
                       'phone': request.user.get_profile().phone,
                       'gender': request.user.get_profile().gender}

            additional_info_form = AbonementsAdditionalInfoForm(offer=offer, initial=initial)
            buy_form = BuyOfferForm(user=request.user, offer=offer)
        context['additional_info_form'] = additional_info_form
        context['buy_form'] = buy_form
        return render_to_response('offers/buy_abonements_additional_info.html', context)
    elif offer.is_additional_service():
        #Мы имеем дело с дополнительной услугой к договору
        if request.method == 'POST':
            additional_info_form = AbonementsClubCardForm(request.POST, offer=offer)
            buy_form = BuyOfferForm(request.POST, user=request.user, offer=offer, initial={'quantity':1})
            if additional_info_form.is_valid() and buy_form.is_valid():
                additional_info_form.save()
                order = AdditionalServicesOrder(offer=offer, user=request.user, visitor_info=request.session['visitor_info'], additional_info=additional_info_form.instance)
                if buy_form.cleaned_data['payment_type'] == 1:
                    #Если выбрали оплату с депозита, сразу списываем деньги и завершаем заказ
                    order.price = offer.coupon_price_money
                    order.price_type = 1
                    order.save()
                    profile = request.user.get_profile()
                    transaction = profile.withdraw_money_deposit(order.price, u"Оплата заказа %s (%s)" % (order.pk, offer.title,))
                    order.complete(transaction)
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return redirect('cabinet_abonements')
                elif buy_form.cleaned_data['payment_type'] == 2:
                    #Аналогично с оплатой бонусами
                    order.price = offer.coupon_price_bonuses
                    order.price_type = 2
                    order.save()
                    profile = request.user.get_profile()
                    transaction = profile.withdraw_bonuses(order.price, u"Оплата заказа %s (%s)" % (order.pk, offer.title,))
                    order.complete(transaction)
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return redirect('cabinet_additional_services')
                elif buy_form.cleaned_data['payment_type'] == 3:
                    order.price = offer.coupon_price_money
                    order.price_type = 1
                    order.save()
                    payment_request = PaymentRequest(inner_transaction=order, amount=order.price, comment=u"Bonus-House.ru. Оплата заказа #%s. Пользователь #%s" % (order.pk, order.user.pk,))
                    payment_request.save()
                    context = RequestContext(request)
                    context['amount'] = order.price
                    context['nickname'] = request.user.email
                    context['order_id'] = payment_request.pk
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return render_to_response('payments/dol/redirect_form.html', context)
        else:
            additional_info_form = AbonementsClubCardForm(offer=offer)
            buy_form = BuyOfferForm(user=request.user, offer=offer)
        context['additional_info_form'] = additional_info_form
        context['buy_form'] = buy_form
        return render_to_response('offers/buy_abonements_club_card.html', context)
    else:
        #Это не абонемент и не доп. услуги, а обычная акция
        if request.method == 'POST':
            buy_form = BuyOfferForm(request.POST, user=request.user, offer=offer)
            if buy_form.is_valid():
                #@TODO: Протестировать определение реферера и узнать время, на которое его надо запоминать в сессии.
                order = Order(offer=offer, quantity=buy_form.cleaned_data['quantity'], user=request.user, visitor_info=request.session['visitor_info'])
                if buy_form.cleaned_data['payment_type'] == 1:
                    #Если выбрали оплату с депозита, сразу списываем деньги и завершаем заказ
                    order.price = offer.coupon_price_money * buy_form.cleaned_data['quantity']
                    order.price_type = 1
                    order.save()
                    profile = request.user.get_profile()
                    transaction = profile.withdraw_money_deposit(order.price, u"Оплата заказа %s (%s)" % (order.pk, offer.title,))
                    order.complete(transaction)
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return redirect('cabinet')
                elif buy_form.cleaned_data['payment_type'] == 2:
                    #Аналогично с оплатой бонусами
                    order.price = offer.coupon_price_bonuses * buy_form.cleaned_data['quantity']
                    order.price_type = 2
                    order.save()
                    profile = request.user.get_profile()
                    transaction = profile.withdraw_bonuses(order.price, u"Оплата заказа %s (%s)" % (order.pk, offer.title,))
                    order.complete(transaction)
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return redirect('cabinet')
                elif buy_form.cleaned_data['payment_type'] == 3:
                    order.price = offer.coupon_price_money * buy_form.cleaned_data['quantity']
                    order.price_type = 1
                    order.save()
                    payment_request = PaymentRequest(inner_transaction=order, amount=order.price, comment=u"Bonus-House.ru. Оплата заказа #%s. Пользователь #%s" % (order.pk, order.user.pk,))
                    payment_request.save()
                    context = RequestContext(request)
                    context['amount'] = order.price
                    context['nickname'] = request.user.email
                    context['order_id'] = payment_request.pk
                    if cart_item is not None:
                        cart.remove_item(cart_item['id'])
                    return render_to_response('payments/dol/redirect_form.html', context)
        else:
            if cart_item is not None:
                initial = {'quantity':cart_item['quantity']}
            else:
                initial = None
            initial = {'first_name': request.user.first_name,
                       'last_name': request.user.last_name,
                       'email': request.user.email,
                       'birth_date': request.user.get_profile().birth_date,
                       'phone': request.user.get_profile().phone,
                       'gender': request.user.get_profile().gender}

            additional_info_form = SimpleActionAdditionalInfoForm(offer=offer, initial=initial)
            context['additional_info_form'] = additional_info_form
            buy_form = BuyOfferForm(user=request.user, offer=offer, initial=initial)
            context['buy_form'] = buy_form
            return render_to_response('offers/buy_simple_actions_additional_info.html', context)


def buy_gift_view(request, offer, cart_item):
    context = RequestContext(request)
    context['offer'] = offer
    cart = ShoppingCart(request)
    if request.method == 'POST':
        additional_info_form = GiftOfferForm(request.POST)
        buy_form = BuyOfferForm(request.POST, user=request.user, offer=offer, initial={'quantity':1}, is_gift=True)
        if additional_info_form.is_valid() and buy_form.is_valid():
            #TODO: Сделать здесь отдельный вид заказов GiftOrder. После использования кода GiftOrder и создается заказ соответствующий акции. Либо придумать что-то получше.
            gift_order = GiftOrder(offer=offer, user=request.user, visitor_info=request.session['visitor_info'])
            gift_order.gift_from_name = additional_info_form.cleaned_data['from_who']
            gift_order.gift_to_name = additional_info_form.cleaned_data['to_who']
            gift_order.gift_delivery_type = additional_info_form.cleaned_data['delivery_type']
            if gift_order.gift_delivery_type == 'email':
                gift_order.gift_delivery_email = additional_info_form.cleaned_data['delivery_email']
            gift_order.gift_message = additional_info_form.cleaned_data['message']
            if buy_form.cleaned_data['payment_type'] == 1:
                #Если выбрали оплату с депозита, сразу списываем деньги и завершаем заказ
                gift_order.price = offer.coupon_price_money
                gift_order.price_type = 1
                gift_order.save()
                profile = request.user.get_profile()
                transaction = profile.withdraw_money_deposit(gift_order.price, u"Оплата заказа подарка %s (%s)" % (gift_order.pk, offer.title,))
                gift_order.complete(transaction)
                if cart_item is not None:
                    cart.remove_item(cart_item['id'])
                return redirect('cabinet_gifts')
            elif buy_form.cleaned_data['payment_type'] == 2:
                #Аналогично с оплатой бонусами
                gift_order.price = offer.coupon_price_bonuses
                gift_order.price_type = 2
                gift_order.save()
                profile = request.user.get_profile()
                transaction = profile.withdraw_bonuses(gift_order.price, u"Оплата заказа подарка %s (%s)" % (gift_order.pk, offer.title,))
                gift_order.complete(transaction)
                if cart_item is not None:
                    cart.remove_item(cart_item['id'])
                return redirect('cabinet_gifts')
            elif buy_form.cleaned_data['payment_type'] == 3:
                gift_order.price = offer.coupon_price_money
                gift_order.price_type = 1
                gift_order.save()
                payment_request = PaymentRequest(inner_transaction=gift_order, amount=gift_order.price, comment=u"Bonus-House.ru. Оплата заказа #%s. Пользователь #%s" % (gift_order.pk, gift_order.user.pk,))
                payment_request.save()
                context = RequestContext(request)
                context['amount'] = gift_order.price
                context['nickname'] = request.user.email
                context['order_id'] = payment_request.pk
                if cart_item is not None:
                    cart.remove_item(cart_item['id'])
                return render_to_response('payments/dol/redirect_form.html', context)
    else:
        initial = None
        additional_info_form = GiftOfferForm(initial=initial)
        buy_form = BuyOfferForm(user=request.user, offer=offer, is_gift=True)
        if offer.is_additional_service():
            messages.warning(request, '<span class="color_red">Внимание! Вы не можете подарить данную услугу тому, кто НЕ является клиентом сети Fitness House!</span> Для активации подарочного купона потребуется действующий номер карты (или договора)')
    context['additional_info_form'] = additional_info_form
    context['buy_form'] = buy_form
    return render_to_response('offers/buy_gift_additional_info.html', context)


def cart_remove(request, item_id):
    cart = ShoppingCart(request)
    cart.remove_item(int(item_id))
    messages.info(request, 'Товар удален из корзины')
    return redirect('cart')


@login_required
@csrf_exempt
def like(request, offer_id):
    offer_id = int(offer_id)
    offer = get_object_or_404(Offers.all_objects, pk=offer_id)
    if request.method == 'POST':
        likes_count = toggle_like(offer, request.user)
        result = {}
        result['success'] = True
        result['new_count'] = likes_count
        return HttpResponse(simplejson.dumps(result))
    return redirect(offer.get_url())

@login_required
@csrf_exempt
def share_vk(request, offer_id):
    if request.method == 'POST' and request.is_ajax():
        offer = get_object_or_404(Offers, id=offer_id)
        profile = request.user.get_profile()
        if not offer in profile.offers_share.all():
            profile.offers_share.add(offer)
            bonus_amount = Settings.objects.get(key='REPOST_BONUS_COUNT').value
            profile.deposit_bonuses(bonus_amount, u'Бонусы за репост %s' % offer.title)
            message = u'Поздравляем! Вам начислено %s бонусов! Бонусы начисляются только один раз за каждую акцию!' % bonus_amount
            return HttpResponse(message)
    return HttpResponse()


@csrf_exempt
@login_required
def ajax_additional_info_club_card_validate(request, offer_id):
    if request.method == 'POST':
        offer = get_object_or_404(Offers, pk=offer_id)
        form = AbonementsClubCardForm(request.POST, offer=offer)
        result = {}
        if form.is_valid():
            tomorrow = now() + datetime.timedelta(days=1)
            result['success'] = True
            context = RequestContext(request)
            context['offer'] = offer
            context['address'] = form.cleaned_data['address']
            context.update(form.cleaned_data)
            context['add_date'] = tomorrow
            context['valid_term'] = u'с %s по %s' % (timezone.localtime((now()+datetime.timedelta(days=1))).strftime('%d.%m.%Y'), timezone.localtime(((now()+datetime.timedelta(days=offer.additional_services_term + 1))).strftime('%d.%m.%Y')))
            result['message'] = render_to_string('offers/_additional_services_buy_preview.html', context)
        else:
            result['success'] = False
            context = {}
            context['form'] = form
            result['message'] = render_to_string('_form_errors.html', context)
        return HttpResponse(simplejson.dumps(result))
    else:
        return redirect('home')


@csrf_exempt
@login_required
def ajax_additional_info_club_card_load_clubs(request, offer_id):
    """Используется при вводе доп. информации к абонементу для подгрузки клубов в зависимости от номера карты"""
    if request.method == 'POST' and request.is_ajax():
        result = {}
        offer = get_object_or_404(Offers, pk=offer_id)
        card_number = request.POST.get('card_number')
        if not card_number:
            result['success'] = False
            result['message'] = 'Вы не ввели номер карты или договора'
        else:
            clubs = get_clubs_by_card_number(card_number)
            if not clubs:
                result['success'] = False
                result['message'] = 'Номер карты не опознан. Проверьте правильность ввода'
            else:
                appliable_clubs = []
                for club in clubs:
                    if club in offer.addresses.all():
                        appliable_clubs.append(club)
                if len(appliable_clubs):
                    result['success'] = True
                    result['clubs'] = []
                    for club in appliable_clubs:
                        result['clubs'].append([club.pk, club.title])
                else:
                    result['success'] = False
                    result['message'] = 'К сожалению, эта акция не распространяется на ваш клуб'
        return HttpResponse(simplejson.dumps(result))
    else:
        return redirect('home')


@csrf_exempt
@login_required
def ajax_additional_info_abonements_validate(request, offer_id):
    if request.method == 'POST':
        offer = get_object_or_404(Offers, pk=offer_id)
        form = AbonementsAdditionalInfoForm(request.POST, offer=offer)
        result = {}
        if form.is_valid():
            tomorrow = now() + datetime.timedelta(days=1)
            result['success'] = True
            context = RequestContext(request)
            context['offer'] = offer
            context['address'] = form.cleaned_data['address']
            context.update(form.cleaned_data)
            context['add_date'] = tomorrow
            context['valid_term'] = u'с %s по %s' % (timezone.localtime(context['add_date']).strftime('%d.%m.%Y'), timezone.localtime((context['add_date'] + datetime.timedelta(days=offer.abonements_term))).strftime('%d.%m.%Y'))
            result['message'] = render_to_string('offers/_additional_services_buy_preview.html', context)
        else:
            result['success'] = False
            context = {}
            context['form'] = form
            result['message'] = render_to_string('_form_errors.html', context)
        return HttpResponse(simplejson.dumps(result))
    else:
        return redirect('home')


@csrf_exempt
@login_required
def ajax_additional_info_simple_actions_validate(request, offer_id):
    if request.method == 'POST':
        offer = get_object_or_404(Offers, pk=offer_id)
        form = SimpleActionAdditionalInfoForm(request.POST, offer=offer)
        result = {}
        if form.is_valid():
            tomorrow = now() + datetime.timedelta(days=1)
            result['success'] = True
            context = RequestContext(request)
            context['offer'] = offer
            context.update(form.cleaned_data)
            context['add_date'] = tomorrow
            # context['valid_term'] = u'с %s по %s' % (timezone.localtime(context['add_date']).strftime('%d.%m.%Y'), timezone.localtime((context['add_date'] + datetime.timedelta(days=offer.abonements_term))).strftime('%d.%m.%Y'))
            result['message'] = render_to_string('offers/_simple_actions_buy_preview.html', context)
        else:
            result['success'] = False
            context = {}
            context['form'] = form
            result['message'] = render_to_string('_form_errors.html', context)
        return HttpResponse(simplejson.dumps(result))
    else:
        return redirect('home')