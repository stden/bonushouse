def update_last_viewed_offers(request, offer):
    last_viewed_offers = request.session.get('last_viewed_offers', [])
    if offer not in last_viewed_offers:
        last_viewed_offers.append(offer)
        if len(last_viewed_offers) > 4:
            last_viewed_offers = last_viewed_offers[-4:]
        request.session['last_viewed_offers'] = last_viewed_offers