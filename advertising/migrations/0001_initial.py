# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Banner'
        db.create_table('advertising_banner', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('banner', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('show_start_date', self.gf('django.db.models.fields.DateField')()),
            ('show_end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('show_max_count', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('click_max_count', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('is_published', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('add_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('clicks', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('impressions', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('advertising', ['Banner'])

        # Adding model 'BannerImpressions'
        db.create_table('advertising_bannerimpressions', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('banner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['advertising.Banner'])),
            ('visitor_info', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['visitor_tracking.VisitorInfo'])),
            ('add_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('advertising', ['BannerImpressions'])

        # Adding model 'BannerClicks'
        db.create_table('advertising_bannerclicks', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('banner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['advertising.Banner'])),
            ('visitor_info', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['visitor_tracking.VisitorInfo'])),
            ('add_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('advertising', ['BannerClicks'])


    def backwards(self, orm):
        # Deleting model 'Banner'
        db.delete_table('advertising_banner')

        # Deleting model 'BannerImpressions'
        db.delete_table('advertising_bannerimpressions')

        # Deleting model 'BannerClicks'
        db.delete_table('advertising_bannerclicks')


    models = {
        'advertising.banner': {
            'Meta': {'object_name': 'Banner'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'banner': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'click_max_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'clicks': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'impressions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'show_end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'show_max_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'show_start_date': ('django.db.models.fields.DateField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'advertising.bannerclicks': {
            'Meta': {'object_name': 'BannerClicks'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'banner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertising.Banner']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'visitor_info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['visitor_tracking.VisitorInfo']"})
        },
        'advertising.bannerimpressions': {
            'Meta': {'object_name': 'BannerImpressions'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'banner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertising.Banner']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'visitor_info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['visitor_tracking.VisitorInfo']"})
        },
        'visitor_tracking.visitorinfo': {
            'Meta': {'object_name': 'VisitorInfo'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'referer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['advertising']