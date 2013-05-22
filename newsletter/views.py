# Create your views here.
import datetime
import csv

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db import models
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from common.forms import CategoriesForm, PhotoForm
from common.models import Categories
from seo.forms import SeoModelMetaForm, SeoModelUrlForm
from offers.forms import OffersForm, ProlongationOffersAdminForm
from offers.models import Offers, ProlongationOffers, Order, AbonementOrder, AdditionalServicesOrder, MetaOrder, GiftOrder
from partners.models import Partner, PartnerAddress, PartnersPage, ClubCardNumbers
from partners.forms import PartnerForm, PartnerAddressForm, PartnersPageForm, ClubCardNumbersForm
from flatpages.models import FlatPage
from flatpages.forms import FlatPageForm
from news.models import News
from news.forms import NewsForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from administration.forms import BulkOffersForm, BulkCategoriesForm, BulkPartnersForm, BulkPagesForm, BulkBannersForm, \
    BulkAuctionsForm, DateRangeForm, IdeaRewardForm, BulkFeedbacksForm, UserForm, BulkUsersForm, BulkPartnersPageForm, \
    BulkClubCardNumbersForm, CallMeSubjectForm, BulkProlongationOffersForm
from django.http import Http404, HttpResponse

from django.core.urlresolvers import reverse_lazy

from django.conf import settings




def unsubscribe(request, user_hash):
    return HttpResponse()