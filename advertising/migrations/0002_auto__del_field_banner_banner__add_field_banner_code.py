# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Banner.banner'
        db.delete_column('advertising_banner', 'banner')

        # Adding field 'Banner.code'
        db.add_column('advertising_banner', 'code',
                      self.gf('ckeditor.fields.RichTextField')(default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Banner.banner'
        db.add_column('advertising_banner', 'banner',
                      self.gf('django.db.models.fields.files.ImageField')(default='', max_length=100),
                      keep_default=False)

        # Deleting field 'Banner.code'
        db.delete_column('advertising_banner', 'code')


    models = {
        'advertising.banner': {
            'Meta': {'object_name': 'Banner'},
            'add_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'click_max_count': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'clicks': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'code': ('ckeditor.fields.RichTextField', [], {}),
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