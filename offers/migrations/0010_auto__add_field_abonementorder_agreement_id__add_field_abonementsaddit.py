# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'AbonementOrder.agreement_id'
        db.add_column('offers_abonementorder', 'agreement_id',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True),
                      keep_default=False)

        # Adding field 'AbonementsAdditionalInfo.gender'
        db.add_column('offers_abonementsadditionalinfo', 'gender',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'AbonementsAdditionalInfo.passport_code'
        db.add_column('offers_abonementsadditionalinfo', 'passport_code',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=30),
                      keep_default=False)

        # Adding field 'AbonementsAdditionalInfo.passport_number'
        db.add_column('offers_abonementsadditionalinfo', 'passport_number',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=30),
                      keep_default=False)

        # Adding field 'AbonementsAdditionalInfo.birth_date'
        db.add_column('offers_abonementsadditionalinfo', 'birth_date',
                      self.gf('django.db.models.fields.DateField')(default=datetime.date(day=1, month=1, year=1990)),
                      keep_default=False)

        # Adding field 'AbonementsAdditionalInfo.how_do_you_know'
        db.add_column('offers_abonementsadditionalinfo', 'how_do_you_know',
                      self.gf('django.db.models.fields.IntegerField')(default=4),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'AbonementOrder.agreement_id'
        db.delete_column('offers_abonementorder', 'agreement_id')

        # Deleting field 'AbonementsAdditionalInfo.gender'
        db.delete_column('offers_abonementsadditionalinfo', 'gender')

        # Deleting field 'AbonementsAdditionalInfo.passport_code'
        db.delete_column('offers_abonementsadditionalinfo', 'passport_code')

        # Deleting field 'AbonementsAdditionalInfo.passport_number'
        db.delete_column('offers_abonementsadditionalinfo', 'passport_number')

        # Deleting field 'AbonementsAdditionalInfo.birth_date'
        db.delete_column('offers_abonementsadditionalinfo', 'birth_date')

        # Deleting field 'AbonementsAdditionalInfo.how_do_you_know'
        db.delete_column('offers_abonementsadditionalinfo', 'how_do_you_know')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'bonushouse.userfeedbacks': {
            'Meta': {'ordering': "('-add_date',)", 'object_name': 'UserFeedbacks'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'admin_reply': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'content_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'bonushouse.userratings': {
            'Meta': {'ordering': "('-add_date',)", 'unique_together': "(('user', 'content_type', 'content_id'),)", 'object_name': 'UserRatings'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'content_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rating': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'common.categories': {
            'Meta': {'object_name': 'Categories'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'common.metrostations': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MetroStations'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'common.uploadedfile': {
            'Meta': {'object_name': 'UploadedFile'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'offers.abonementorder': {
            'Meta': {'object_name': 'AbonementOrder'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'additional_info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.AbonementsAdditionalInfo']"}),
            'agreement_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'barcode': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'offer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Offers']"}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'price_type': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'transaction_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'transaction_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'visitor_info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['visitor_tracking.VisitorInfo']", 'null': 'True', 'blank': 'True'})
        },
        'offers.abonementsadditionalinfo': {
            'Meta': {'object_name': 'AbonementsAdditionalInfo'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['partners.PartnerAddress']", 'null': 'True', 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'father_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gender': ('django.db.models.fields.IntegerField', [], {}),
            'how_do_you_know': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'passport_code': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'passport_number': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'offers.couponcodes': {
            'Meta': {'object_name': 'CouponCodes'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_used': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['partners.Partner']"}),
            'used_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'offers.offers': {
            'Meta': {'object_name': 'Offers'},
            'abonements_is_multicard': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'addresses': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['partners.PartnerAddress']", 'symmetrical': 'False'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['common.Categories']", 'symmetrical': 'False'}),
            'coupon_price_bonuses': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'coupon_price_money': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'discount_price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'money_bonuses_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['partners.Partner']", 'null': 'True', 'blank': 'True'}),
            'photos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['common.UploadedFile']", 'symmetrical': 'False'}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '100'}),
            'short_description': ('django.db.models.fields.TextField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'terms': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'offers.order': {
            'Meta': {'object_name': 'Order'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'coupon_codes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['offers.CouponCodes']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'offer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offers.Offers']"}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'price_type': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'transaction_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'transaction_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'visitor_info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['visitor_tracking.VisitorInfo']", 'null': 'True', 'blank': 'True'})
        },
        'partners.partner': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Partner'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'photos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['common.UploadedFile']", 'symmetrical': 'False'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'partners.partneraddress': {
            'Meta': {'object_name': 'PartnerAddress'},
            'address': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'fitnesshouse_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'geocode_latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'geocode_longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metro': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['common.MetroStations']", 'null': 'True', 'blank': 'True'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['partners.Partner']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'schedule': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'visitor_tracking.visitorinfo': {
            'Meta': {'object_name': 'VisitorInfo'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'referer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['offers']
