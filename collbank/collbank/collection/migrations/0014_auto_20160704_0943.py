# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-04 07:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0013_auto_20160629_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessmedium',
            name='format',
            field=models.CharField(choices=[('2', 'CDROM'), ('3', 'DVD'), ('4', 'blueray'), ('5', 'hard disk'), ('1', 'internet'), ('8', 'other'), ('6', 'paper copy'), ('7', 'video')], default='0', help_text='Sorry, no help available for access.medium.format', max_length=5, verbose_name='Resource medium'),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='type',
            field=models.CharField(choices=[('1', 'No Linguistic Annotation'), ('25', 'PosTagging'), ('2', 'alignment'), ('3', 'audienceReactions'), ('4', 'bodyMovements'), ('5', 'certaintyLevel'), ('6', 'coreference'), ('7', 'dialogueActs'), ('8', 'discourseAnnotation'), ('9', 'discourseRelations'), ('10', 'events'), ('11', 'facialExpressions'), ('12', 'gazeEyeMovements'), ('13', 'glosses'), ('14', 'handArmGestures'), ('15', 'handManipulationOfObjects'), ('16', 'headMovements'), ('17', 'lemmatization'), ('18', 'links'), ('19', 'lipMovements'), ('20', 'namedEntities'), ('21', 'orthographicTranscription'), ('52', 'other'), ('22', 'paralanguageAnnotation'), ('23', 'phoneticTranscription'), ('24', 'polarity'), ('26', 'prompts'), ('27', 'prosodicAnnotation'), ('28', 'questionTopicalTarget'), ('29', 'segmentation'), ('30', 'semanticAnnotation'), ('31', 'semanticClasses'), ('32', 'semanticRelations'), ('33', 'semanticRoles'), ('34', 'sentiment'), ('35', 'sentityMentions'), ('36', 'shallowParsing'), ('37', 'soundEvents'), ('38', 'soundToTextAlignment'), ('39', 'speakerIdentification'), ('40', 'speakerTurns'), ('41', 'speechActs'), ('42', 'speechAnnotation'), ('43', 'stemming'), ('44', 'structuralAnnotation'), ('45', 'subcategorizationFrames'), ('53', 'syntacticAnnotation'), ('46', 'temporalExpressions'), ('47', 'textualEntailment'), ('48', 'translation'), ('49', 'transliteration'), ('50', 'treebanks'), ('51', 'wordSenses')], default='0', max_length=5, verbose_name='Kind of annotation'),
        ),
        migrations.AlterField(
            model_name='mediaformat',
            name='name',
            field=models.CharField(choices=[('1', 'application/pdf'), ('2', 'application/smil+xml'), ('3', 'audio/x-aiff'), ('4', 'audio/x-mp2'), ('5', 'audio/x-mp3'), ('6', 'audio/x-mpeg4'), ('7', 'audio/x-wav'), ('11', 'image/gif'), ('8', 'image/jpeg'), ('9', 'image/png'), ('10', 'image/tiff'), ('20', 'other'), ('14', 'text/folia'), ('12', 'text/html'), ('13', 'text/tei'), ('21', 'unknown'), ('18', 'video/quicktime'), ('15', 'video/x-mpeg1'), ('16', 'video/x-mpeg2'), ('17', 'video/x-mpeg4'), ('19', 'video/x-msvideo')], default='0', help_text="See: <a href='http://hdl.handle.net/11459/CCR_C-2571_2be2e583-e5af-34c2-3673-93359ec1f7df'>Format of this resource medium</a>", max_length=5, verbose_name='Format of a medium'),
        ),
    ]