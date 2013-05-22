# -*- coding: utf-8 -*-
# Create your views here.
from bonushouse.models import UserProfile
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404



def unsubscribe(request, user_hash):
    try:
        profile = UserProfile.objects.get(subscribe_hash=str(user_hash))
        profile.subscribe_hash = None
        context = RequestContext(request)
        return render_to_response('_newsletter_unsubscribe.html',context)
    except UserProfile.DoesNotExist:
        return redirect('home')