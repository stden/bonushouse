# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'NewsletterCampaign'
        db.create_table('newsletter_newslettercampaign', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('gender', self.gf('django.db.models.fields.IntegerField')()),
            ('min_age', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('max_age', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('include_users_with_no_age', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('min_bonuses_ballance', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('offer_participation', self.gf('django.db.models.fields.IntegerField')()),
            ('auction_participation', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('newsletter', ['NewsletterCampaign'])

        # Adding model 'NewsletterEmail'
        db.create_table('newsletter_newsletteremail', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('text', self.gf('ckeditor.fields.RichTextField')()),
            ('send_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('is_sent', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('newsletter', ['NewsletterEmail'])

        # Adding M2M table for field campaigns on 'NewsletterEmail'
        db.create_table('newsletter_newsletteremail_campaigns', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('newsletteremail', models.ForeignKey(orm['newsletter.newsletteremail'], null=False)),
            ('newslettercampaign', models.ForeignKey(orm['newsletter.newslettercampaign'], null=False))
        ))
        db.create_unique('newsletter_newsletteremail_campaigns', ['newsletteremail_id', 'newslettercampaign_id'])


    def backwards(self, orm):
        # Deleting model 'NewsletterCampaign'
        db.delete_table('newsletter_newslettercampaign')

        # Deleting model 'NewsletterEmail'
        db.delete_table('newsletter_newsletteremail')

        # Removing M2M table for field campaigns on 'NewsletterEmail'
        db.delete_table('newsletter_newsletteremail_campaigns')


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
        }
    }

    complete_apps = ['newsletter']