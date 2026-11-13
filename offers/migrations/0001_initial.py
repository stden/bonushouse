# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Offers'
        db.create_table('offers_offers', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('partner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['partners.Partner'], null=True, blank=True)),
            ('quantity', self.gf('django.db.models.fields.PositiveIntegerField')(default=100)),
            ('initial_price', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('discount_price', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('coupon_price_money', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('coupon_price_bonuses', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('money_bonuses_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('short_description', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('terms', self.gf('django.db.models.fields.TextField')()),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('is_published', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('add_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('offers', ['Offers'])

        # Adding M2M table for field categories on 'Offers'
        db.create_table('offers_offers_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('offers', models.ForeignKey(orm['offers.offers'], null=False)),
            ('categories', models.ForeignKey(orm['common.categories'], null=False))
        ))
        db.create_unique('offers_offers_categories', ['offers_id', 'categories_id'])

        # Adding M2M table for field photos on 'Offers'
        db.create_table('offers_offers_photos', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('offers', models.ForeignKey(orm['offers.offers'], null=False)),
            ('uploadedfile', models.ForeignKey(orm['common.uploadedfile'], null=False))
        ))
        db.create_unique('offers_offers_photos', ['offers_id', 'uploadedfile_id'])

        # Adding model 'Order'
        db.create_table('offers_order', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('visitor_info', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['visitor_tracking.VisitorInfo'], null=True, blank=True)),
            ('offer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['offers.Offers'])),
            ('quantity', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('price', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('price_type', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('is_completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('transaction_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('transaction_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('add_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('offers', ['Order'])

        # Adding M2M table for field coupon_codes on 'Order'
        db.create_table('offers_order_coupon_codes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('order', models.ForeignKey(orm['offers.order'], null=False)),
            ('couponcodes', models.ForeignKey(orm['offers.couponcodes'], null=False))
        ))
        db.create_unique('offers_order_coupon_codes', ['order_id', 'couponcodes_id'])

        # Adding model 'CouponCodes'
        db.create_table('offers_couponcodes', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('partner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['partners.Partner'])),
            ('is_used', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('used_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('offers', ['CouponCodes'])


    def backwards(self, orm):
        # Deleting model 'Offers'
        db.delete_table('offers_offers')

        # Removing M2M table for field categories on 'Offers'
        db.delete_table('offers_offers_categories')

        # Removing M2M table for field photos on 'Offers'
        db.delete_table('offers_offers_photos')

        # Deleting model 'Order'
        db.delete_table('offers_order')

        # Removing M2M table for field coupon_codes on 'Order'
        db.delete_table('offers_order_coupon_codes')

        # Deleting model 'CouponCodes'
        db.delete_table('offers_couponcodes')


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
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['common.Categories']", 'symmetrical': 'False'}),
            'coupon_price_bonuses': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'coupon_price_money': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'discount_price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'money_bonuses_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['partners.Partner']", 'null': 'True', 'blank': 'True'}),
            'photos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['common.UploadedFile']", 'symmetrical': 'False'}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '100'}),
            'short_description': ('django.db.models.fields.TextField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'terms': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'metro': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['common.MetroStations']", 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'photos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['common.UploadedFile']", 'symmetrical': 'False'}),
            'schedule': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
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