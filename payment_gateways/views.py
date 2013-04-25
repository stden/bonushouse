# -*- coding: utf-8 -*-
# Create your views here.
from payment_gateways.models import DummyPaymentInfo, PaymentRequest, DolPaymentInfo
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.conf import settings
import md5
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

@csrf_exempt
def complete_payment(request, backend):
    if backend == 'dummy' and settings.DEBUG:
        payment_request_id = request.GET.get('order_id')
        amount = request.GET.get('amount')
        secret = request.GET.get('secret')
        if amount and payment_request_id and secret == 'secret':
            payment_request = get_object_or_404(PaymentRequest, pk=payment_request_id, is_completed=False, amount=amount)
            payment_info = DummyPaymentInfo()
            payment_info.save()
            payment_request.inner_transaction.complete(payment_request)
            payment_request.complete(payment_info)
            return HttpResponse('OK')
        else:
            return HttpResponse('PARAMS CHECK FAILED')
    elif backend == 'dol':
        message = ''
        for key in request.POST:
            message += '%s:%s;' % (key, request.POST[key])
        try:
            amount = request.POST.get('amount')
            userid = request.POST.get('userid')
            paymentid = int(request.POST.get('paymentid'))
            orderid = int(request.POST.get('orderid'))
            paymode = request.POST.get('paymode')
        except:
            amount = None
            userid = None
            paymentid = None
            orderid = None
            paymode = None
        key = request.POST.get('key')
        if not amount or not userid or not paymentid or not key or not paymode:
            status = 'NO'
            id = userid
            comment = 'Отсутствуют необходимые параметры'
        else:
            payment_info = DolPaymentInfo(amount=amount, userid=userid, paymentid=paymentid, key=key, paymode=paymode)
            payment_info.save()
            try:
                payment_request = PaymentRequest.objects.get(pk=orderid)
                security_key = settings.DOL_SECRET_KEY
                my_key = md5.new(str(amount)+userid+str(paymentid)+security_key).hexdigest()
                if my_key == key:
                    if payment_request.amount == int(float(amount)):
                        if not payment_request.is_completed:
                            status = 'YES'
                            #Если оплата еще не совершалась
                            payment_request.inner_transaction.complete(payment_request)
                            payment_request.complete(payment_info)
                            id = payment_request.pk
                            comment = 'Платеж найден. Оплата произведена успешно.'
                        else:
                            status = 'YES'
                            #Оплата уже совершена. Просто отвечаем, что платеж найден в базе
                            id = payment_request.pk
                            comment = 'Платеж найден в базе. Оплата уже осуществлялась ранее.'
                    else:
                        id = payment_request.pk
                        status = 'NO'
                        comment = 'Сумма не совпадает со стоимостью заказа'
                else:
                    #Не совпадает ключ безопасности
                    id = userid
                    status = 'NO'
                    comment = 'Контрольные подписи не совпадают'
            except PaymentRequest.DoesNotExist:
                #ЗАказ не найден в базе
                status = 'NO'
                comment = 'Заказ не найден в базе проекта'
                id = userid
            payment_info.status = status
            payment_info.comment = comment
            payment_info.save()
        context = {}
        context['status'] = status
        context['id'] = id
        context['comment'] = comment
        result = render_to_response('payments/dol/payment_completion.xml', context)
        return result
    else:
        raise Http404

@csrf_exempt
def check_order_id(request, backend):
    message = ''
    for key in request.POST:
        message += '%s:%s;' % (key, request.POST[key])

    if backend == 'dol':
        context = {}
        security_key = settings.DOL_SECRET_KEY
        order_id = request.POST.get('userid')
        key = request.POST.get('key')
        if order_id is None or key is None:
            code = 'NO'
            comment = 'Отсутствуют необходимые параметры в запросе'
        else:
            my_key = md5.new('0'+order_id+'0'+security_key).hexdigest()
            if my_key == key:
                users = User.objects.filter(email=order_id)
                if users.count():
                    code = 'YES'
                    comment = ''
                else:
                    code = 'NO'
                    comment = 'Заказ не найден'
            else:
                code = 'NO'
                comment = 'Не пройдена проверка безопасности'

        context['code'] = code
        context['comment'] = comment
        return render_to_response('payments/dol/check_order.xml', context)

@csrf_exempt
def success_payment(request):
    context = RequestContext(request)
    return render_to_response('payments/success.html', context)

@csrf_exempt
def failed_payment(request):
    context = RequestContext(request)
    request.encoding = 'windows-1251'
    context['err_msg'] = request.GET.get('err_msg[]')
    return render_to_response('payments/failure.html', context)