# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'NewsletterSms'
        db.create_table('newsletter_newslettersms', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')(max_length=140)),
            ('send_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('is_sent', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('newsletter', ['NewsletterSms'])

        # Adding M2M table for field campaigns on 'NewsletterSms'
        db.create_table('newsletter_newslettersms_campaigns', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('newslettersms', models.ForeignKey(orm['newsletter.newslettersms'], null=False)),
            ('newslettercampaign', models.ForeignKey(orm['newsletter.newslettercampaign'], null=False))
        ))
        db.create_unique('newsletter_newslettersms_campaigns', ['newslettersms_id', 'newslettercampaign_id'])


    def backwards(self, orm):
        # Deleting model 'NewsletterSms'
        db.delete_table('newsletter_newslettersms')

        # Removing M2M table for field campaigns on 'NewsletterSms'
        db.delete_table('newsletter_newslettersms_campaigns')


    models = {
        'newsletter.newslettercampaign': {
            'Meta': {'object_name': 'NewsletterCampaign'},
            'auction_participation': ('django.db.models.fields.IntegerField', [], {}),
            'gender': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_users_with_no_age': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'max_age': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'min_age': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'min_bonuses_ballance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'offer_participation': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'newsletter.newsletteremail': {
            'Meta': {'object_name': 'NewsletterEmail'},
            'campaigns': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletter.NewsletterCampaign']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_date': ('django.db.models.fields.DateTimeField', [], {}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('ckeditor.fields.RichTextField', [], {})
        },
        'newsletter.newslettersms': {
            'Meta': {'object_name': 'NewsletterSms'},
            'campaigns': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletter.NewsletterCampaign']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_date': ('django.db.models.fields.DateTimeField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {'max_length': '140'})
        }
    }

    complete_apps = ['newsletter']