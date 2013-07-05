# -*- coding: utf-8 -*-
import datetime
from urllib import urlopen

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.timezone import now
from social_auth.signals import pre_update
from django.dispatch import receiver


GENDER_CHOICES = (
    (0, 'жен.'),
    (1, 'муж.'),
)


class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User)
    gender = models.IntegerField(verbose_name='Пол', choices=GENDER_CHOICES, blank=True, null=True)
    birth_date = models.DateField(verbose_name='Дата рождения', blank=True, null=True)
    # avatar = models.ImageField(upload_to='user_avatars/', verbose_name='Фото')
    phone = models.CharField(max_length=32, verbose_name='Контактный телефон', blank=True, null=True)
    #Поля служащие для ускорения выборки
    #@TODO: Добавить функции для пересчета полей ниже
    age = models.PositiveIntegerField(editable=False, blank=True, null=True)
    bonuses_ballance = models.IntegerField(editable=False, default=0)
    auctions_won = models.PositiveIntegerField(editable=False, default=0)
    coupons_bought = models.PositiveIntegerField(editable=False, default=0)
    refered_by = models.ForeignKey(User, editable=False, blank=True, null=True, related_name='referer')
    referer_checked = models.BooleanField(editable=False, default=False)
    subscribe_hash = models.CharField(max_length=255, editable=False, blank=True, null=True)
    offers_share = models.ManyToManyField('offers.Offers', related_name='offers_share',
                                          verbose_name='Акции, которыми поделился пользователь')

    def calculate_age(self):
        if self.birth_date:
            age_delta = datetime.date.today() - self.birth_date
            result = int(age_delta.days / 365.25)
            if result < 0:
                result = 0
            return result
        else:
            return None

    def get_name(self):
        if self.user.get_full_name():
            return self.user.get_full_name()
        else:
            return self.user.username

    def get_gender(self):
        gender = None
        if self.gender == 0:
            gender = 'жен.'
        elif self.gender == 1:
            gender = 'муж.'
        return gender

    def get_bonuses_ballance(self):
        """
        Возвращает количество неиспользованных бонусов у данного пользователя.
        """
        transactions = BonusTransactions.objects.filter(user=self.user, is_completed=True).aggregate(
            models.Sum('amount'))
        if transactions['amount__sum']:
            transactions_sum = transactions['amount__sum']
        else:
            transactions_sum = 0
        return transactions_sum

    def get_money_ballance(self):
        """
        Возвращает количество неиспользованных денег на счету у данного пользователя.
        """
        deposits = AccountDepositTransactions.objects.filter(user=self.user, is_completed=True).aggregate(
            models.Sum('amount'))
        if deposits['amount__sum']:
            transactions_sum = deposits['amount__sum']
        else:
            transactions_sum = 0
        return transactions_sum

    def withdraw_money_deposit(self, amount, comment):
        """Снимает деньги с депозита пользователя"""
        transaction = AccountDepositTransactions(user=self.user, amount=-amount, comment=comment, is_completed=True)
        transaction.save()
        return transaction

    def withdraw_bonuses(self, amount, comment):
        """Снимает бонусы со счета пользователя"""
        transaction = BonusTransactions(user=self.user, amount=-amount, is_completed=True, comment=comment)
        transaction.save()
        return transaction

    def deposit_bonuses(self, amount, comment):
        """Начисляет бонусы на счет пользователя"""
        transaction = BonusTransactions(user=self.user, amount=amount, comment=comment, is_completed=True)
        transaction.save()
        return transaction

    def is_partner(self):
        if self.user.partner_set.count():
            return True
        else:
            return False


#Автоматический расчет бонусов в зависимости от цены купона
#(<Верхний порог цены>, <коэфициент, на который умножать цену, чтобы получить кол-во бонусов>)
AUTO_BONUS_COUNTS = (
    (1000, 0.8),
    (4000, 0.85),
    (8000, 0.9),
    (12000, 0.93),
    (14000, 0.94),
    (18000, 0.95),
    (28000, 0.96),
    (36000, 0.97),
    (48000, 0.98),
    (76000, 0.985),
    (82000, 0.988),
    (94000, 0.989),
    (100000000000000000000000000000, 0.99),
)


class PincodeTransaction(models.Model):
    action_name = models.TextField(verbose_name='Название акции')
    price = models.BigIntegerField(verbose_name='Стоимость')
    consumer = models.ForeignKey(User, verbose_name='Покупатель', related_name='consumer')
    buy_date = models.DateTimeField(verbose_name='Дата покупки')
    maturity_date = models.DateTimeField(verbose_name='Дата погашения')
    operator = models.ForeignKey(User, verbose_name='Оператор', related_name='operator')
    is_gift = models.BooleanField(verbose_name='Куплено в подарок?')
    recipient = models.ForeignKey(User, verbose_name='Получатель подарка', blank=True, null=True,
                                  related_name='recipient')
    add_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    def complete(self):
        self.is_completed = True
        self.save()


class BonusTransactions(models.Model):
    user = models.ForeignKey(User)
    amount = models.IntegerField(verbose_name='Сумма')
    is_completed = models.BooleanField(verbose_name='Оплата завершена', default=False)
    payment_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    payment_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    payment_object = generic.GenericForeignKey("payment_type", "payment_id")
    payment_date = models.DateTimeField(verbose_name='Дата оплаты', blank=True, null=True)
    comment = models.TextField(verbose_name='Комментарий', blank=True, null=True)
    add_date = models.DateTimeField(verbose_name='Дата добавления', editable=False, auto_now_add=True)

    def complete(self, payment_info):
        self.payment_object = payment_info
        self.is_completed = True
        self.payment_date = now()
        self.save()


class AccountDepositTransactions(models.Model):
    user = models.ForeignKey(User)
    amount = models.IntegerField(verbose_name='Сумма')
    is_completed = models.BooleanField(verbose_name='Оплата завершена', default=False)
    payment_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    payment_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    payment_object = generic.GenericForeignKey("payment_type", "payment_id")
    payment_date = models.DateTimeField(verbose_name='Дата оплаты', blank=True, null=True)
    comment = models.TextField(verbose_name='Комментарий', blank=True, null=True)
    add_date = models.DateTimeField(verbose_name='Дата добавления', editable=False, auto_now_add=True)

    def complete(self, payment_info):
        self.payment_object = payment_info
        self.is_completed = True
        self.payment_date = now()
        self.save()


class ApprovedFeedbacksManager(models.Manager):
    def get_query_set(self):
        return super(ApprovedFeedbacksManager, self).get_query_set().filter(is_approved=True)


class NotApprovedFeedbacksManager(models.Manager):
    def get_query_set(self):
        return super(NotApprovedFeedbacksManager, self).get_query_set().filter(is_approved=False)


class UserFeedbacks(models.Model):
    content_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    content_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    content_object = generic.GenericForeignKey("content_type", "content_id")
    text = models.TextField(verbose_name='Текст')
    admin_reply = models.TextField(verbose_name='Ответ администрации', blank=True, null=True)
    user = models.ForeignKey(User, verbose_name='Автор', editable=False)
    add_date = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Дата добавления')
    ratings = generic.GenericRelation('UserRatings', object_id_field='content_id', content_type_field='content_type')
    is_approved = models.BooleanField(editable=False, default=False)
    #Поля для ускорения выборки
    partner_user = models.ForeignKey(User, blank=True, null=True,
                                     related_name='moderated_feedbacks') #Служит для модерации отзывов в меню партнера. Обновляется по post_save
    #Менеджеры
    objects = ApprovedFeedbacksManager()
    moderation_objects = NotApprovedFeedbacksManager()

    def get_author_rating(self):
        if self.ratings.count():
            return self.ratings.all()[0].rating
        else:
            return 3

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы пользователей'
        ordering = ('-add_date',)


class UserRatings(models.Model):
    content_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    content_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    content_object = generic.GenericForeignKey("content_type", "content_id")
    rating = models.PositiveIntegerField(verbose_name='Оценка')
    user = models.ForeignKey(User, verbose_name='Автор', editable=False)
    add_date = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        unique_together = ('user', 'content_type', 'content_id',)
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки пользователей'
        ordering = ('-add_date',)


class BusinessIdea(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Описание идеи')
    attachment = models.FileField(upload_to='ideas/', verbose_name='Прикрепить файл', blank=True, null=True)
    user = models.ForeignKey(User, verbose_name='Автор', editable=False)
    is_reviewed = models.BooleanField(editable=False, verbose_name='Рассмотрено администратором', default=False)
    bonus_reward = models.IntegerField(editable=False, blank=True, null=True)
    bonus_reward_transaction = models.ForeignKey('BonusTransactions', blank=True, null=True, editable=False)
    add_date = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Дата добавления')

    def apply_reward(self, reward):
        """Начисляет автору идеи бонусы и помечает идею, как рассмотренную. Ожидает на входе число бонусов в награду."""
        transaction = self.user.get_profile().deposit_bonuses(reward, u'За идею "%s"' % (self.title,))
        self.bonus_reward = reward
        self.bonus_reward_transaction = transaction
        self.is_reviewed = True
        self.save()

    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.ideas_edit', (), {'idea_id': self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.ideas_delete', (), {'idea_id': self.pk})


class CronFitnesshouseNotifications(models.Model):
    content_type = models.ForeignKey(ContentType, editable=False)
    content_id = models.PositiveIntegerField(editable=False)
    content_object = generic.GenericForeignKey("content_type", "content_id")
    is_completed = models.BooleanField(default=False)
    fitnesshouse_reply = models.TextField(blank=True, null=True)

    def send(self):
        reply = self.content_object.notify_fitnesshouse()
        self.fitnesshouse_reply = reply
        self.is_completed = True
        self.save()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def calculate_age(sender, instance, created, **kwargs):
    if instance.age != instance.calculate_age():
        instance.age = instance.calculate_age()
        instance.save()


def update_bonuses_ballance(sender, instance, created, **kwargs):
    if instance.user.get_profile().bonuses_ballance != instance.user.get_profile().get_bonuses_ballance():
        instance.user.get_profile().bonuses_ballance = instance.user.get_profile().get_bonuses_ballance()
        instance.user.get_profile().save()


@receiver(pre_update)
def update_person_details(sender, **kwargs):
    person = kwargs.get('user')
    details = kwargs.get('details')
    load_person_avatar(sender, person.get_profile(), kwargs.get('response'))


def update_partner_user(sender, instance, created, **kwargs):
    if created:
        if instance.content_type.name == 'partner':
            instance.partner_user = instance.content_object.admin_user
            instance.save()
        elif instance.content_type.name == 'offers':
            instance.partner_user = instance.content_object.partner.admin_user
            instance.save()


def load_person_avatar(sender, person, info):
    image_url = None
    if sender.name == 'vkontakte-oauth2':
        image_url = info.get('user_photo') # If photo is absent user_photo is absent too

    elif sender.name == 'odnoklassniki':
        image_url = info.get('pic_2')
        if 'stub' in image_url: # No real image
            image_url = None

    elif sender.name == 'mailru-oauth2':
        if info.get('has_pic'):
            image_url = info.get('pic_big')

    elif sender.name == 'twitter':
        image_url = info.get('profile_image_url')
        if not image_url:
            image_url = info.get('profile_image_url_https')
        if not 'default_profile' in image_url:
            image_url = image_url.replace('_normal', '_bigger')
        else: # No real image
            image_url = None

    elif sender.name == 'yandex-oauth2':
        image_url = info.get('userpic')

    elif sender.name == 'facebook':
        image_url = 'http://graph.facebook.com/%s/picture?type=large' % info.get('id')

    if image_url:
        image_content = urlopen(image_url)

        # Facebook default image check
        if sender.name == 'facebook' and 'image/gif' in str(image_content.info()):
            return
        image_name = default_storage.get_available_name(
            person.avatar.field.upload_to + '/' + str(person.id) + '.' + image_content.headers.subtype)
        person.avatar.save(image_name, ContentFile(image_content.read()))
        person.save()


def schedule_fitnesshouse_notification(subject):
    cron_task = CronFitnesshouseNotifications(content_object=subject)
    cron_task.save()


post_save.connect(create_user_profile, sender=User)
post_save.connect(calculate_age, sender=UserProfile)
post_save.connect(update_bonuses_ballance, sender=BonusTransactions)
post_save.connect(update_partner_user, sender=UserFeedbacks)
