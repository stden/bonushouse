# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from auctions.models import Auction, AuctionBid
from auctions.forms import AddBidForm, CardNumberForm
from django.utils.timezone import now
import datetime
from django.contrib.auth.decorators import login_required
from bonushouse.models import AccountDepositTransactions
from django.contrib import messages
from dbsettings.models import Settings
from offers.forms import AbonementsAdditionalInfoForm, AbonementsClubCardForm
from django.http import Http404
from bonushouse.models import schedule_fitnesshouse_notification
# Create your views here.

def index(request):
    context = RequestContext(request)
    context['auctions_list'] = Auction.objects.all()
    return render_to_response('auctions/index.html', context)

def view(request, auction_id):
    raise Http404
    auction = get_object_or_404(Auction.all_objects, pk=auction_id)
    context = RequestContext(request)
    context['auction'] = auction
    if auction.is_additional_service():
        if auction.additional_services_get_user_card_number(request.user):
            context['user_card_number'] = auction.additional_services_get_user_card_number(request.user)
        else:
            if request.method == 'POST':
                card_number_form = CardNumberForm(request.POST, auction=auction)
                if card_number_form.is_valid():
                    auction.additional_services_add_user_card_number(request.user, card_number_form.cleaned_data['card_number'])
                    return redirect(auction.get_url())
            else:
                card_number_form = CardNumberForm(auction=auction)
            context['card_number_form'] = card_number_form
    return render_to_response('auctions/view.html', context)

@login_required()
def additional_info(request, auction_id):
    auction = get_object_or_404(Auction.all_objects, pk=auction_id, is_completed=True, winner=request.user)
    if not auction.additional_info_needed():
        raise Http404
    if request.method == 'POST':
        if auction.is_abonement():
            additional_info_form = AbonementsAdditionalInfoForm(request.POST, offer=auction)
            if additional_info_form.is_valid():
                additional_info_form.save()
                auction.abonements_additional_info = additional_info_form.instance
                auction.save()
                schedule_fitnesshouse_notification(auction)
                return redirect('cabinet_auctions')
        elif auction.is_additional_service():
            additional_info_form = AbonementsClubCardForm(request.POST, offer=auction)
            if additional_info_form.is_valid():
                additional_info_form.save()
                auction.additional_services_additional_info = additional_info_form.instance
                auction.save()
                schedule_fitnesshouse_notification(auction)
                return redirect('cabinet_auctions')
    else:
        if auction.is_abonement():
            additional_info_form = AbonementsAdditionalInfoForm(offer=auction)
        elif auction.is_additional_service():
            print auction.additional_services_get_user_card_number(request.user)
            additional_info_form = AbonementsClubCardForm(offer=auction, initial={'card_number':auction.additional_services_get_user_card_number(request.user)})
    context = RequestContext(request)
    context['auction'] = auction
    context['additional_info_form'] = additional_info_form
    return render_to_response('auctions/abonements_additional_info.html', context)

@login_required
def add_bid_form(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id)
    context = RequestContext(request)
    if auction.is_additional_service():
        if auction.additional_services_get_user_card_number(request.user):
            context['user_card_number'] = auction.additional_services_get_user_card_number(request.user)
        else:
            return redirect(auction.get_url())
    context['auction'] = auction
    if request.method == 'POST':
        bid_form = AddBidForm(request.POST, request=request, auction=auction, initial={'amount':auction.get_actual_price()})
        if bid_form.is_valid():
            transaction = AccountDepositTransactions(
                user=request.user,
                amount=-bid_form.cleaned_data['amount'],
                is_completed=True,
                comment=u"Блокировка ставки на аукцион %s" % (auction.title, )
            )
            transaction.save()
            bid = AuctionBid(auction=auction, user=request.user, amount=bid_form.cleaned_data['amount'], transaction=transaction)
            bid.save()
            #Разблокируем перебитые ставки
            auction.unlock_beaten_bids()
            if bid.amount >= auction.buyout_price:
                #Если достигнута цена выкупа, завершаем аукцион
                auction.complete()
                return redirect('cabinet_auctions')
            else:
                #Продлеваем аукцион в соответствии с настройками
                AUCTIONS_BID_ADD_TIME = Settings.objects.get(key='AUCTIONS_BID_ADD_TIME')
                AUCTIONS_BID_ADD_TIME = AUCTIONS_BID_ADD_TIME.value
                auction.end_date += datetime.timedelta(seconds=int(AUCTIONS_BID_ADD_TIME))
                auction.save()
                messages.info(request, 'Спасибо! Ваша ставка принята')
                return redirect(auction.get_url())
    else:
        bid_form = AddBidForm(request=request, auction=auction, initial={'amount':auction.get_actual_price()})
    context['bid_form'] = bid_form
    return render_to_response('auctions/add_bid.html', context)