# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-29 09:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0010_auto_20160627_1631'),
    ]

    operations = [
        migrations.AddField(
            model_name='access',
            name='name',
            field=models.TextField(default='-', verbose_name='Name of this access type'),
        ),
        migrations.AlterField(
            model_name='access',
            name='ISBN',
            field=models.TextField(blank=True, verbose_name='ISBN of collection'),
        ),
        migrations.AlterField(
            model_name='access',
            name='ISLRN',
            field=models.TextField(blank=True, verbose_name='ISLRN of collection'),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='type',
            field=models.CharField(choices=[('1', 'No Linguistic Annotation'), ('2', 'alignment'), ('3', 'discourseAnnotation'), ('4', 'discourseAnnotation-audienceReactions'), ('5', 'discourseAnnotation-coreference'), ('6', 'discourseAnnotation-dialogueActs'), ('7', 'discourseAnnotation-discourseRelations'), ('54', 'erwin'), ('8', 'glosses'), ('9', 'lemmatization'), ('10', 'modalityAnnotation-bodyMovements'), ('11', 'modalityAnnotation-facialExpressions'), ('12', 'modalityAnnotation-gazeEyeMovements'), ('13', 'modalityAnnotation-handArmGestures'), ('14', 'modalityAnnotation-handManipulationOfObjects'), ('15', 'modalityAnnotation-headMovements'), ('16', 'modalityAnnotation-lipMovements'), ('17', 'morphosyntacticAnnotation-bPosTagging'), ('19', 'morphosyntacticAnnotation-posTagging'), ('20', 'namedEntities'), ('53', 'other'), ('18', 'prompts'), ('21', 'segmentation'), ('22', 'semanticAnnotation'), ('23', 'semanticAnnotation-certaintyLevel'), ('25', 'semanticAnnotation-entityMentions'), ('26', 'semanticAnnotation-events'), ('27', 'semanticAnnotation-polarity'), ('28', 'semanticAnnotation-questionTopicalTarget'), ('29', 'semanticAnnotation-semanticClasses'), ('30', 'semanticAnnotation-semanticRelations'), ('31', 'semanticAnnotation-semanticRoles'), ('32', 'semanticAnnotation-speechActs'), ('33', 'semanticAnnotation-temporalExpressions'), ('34', 'semanticAnnotation-textualEntailment'), ('35', 'semanticAnnotation-wordSenses'), ('24', 'sentiment'), ('36', 'speechAnnotation'), ('37', 'speechAnnotation-orthographicTranscription'), ('38', 'speechAnnotation-paralanguageAnnotation'), ('39', 'speechAnnotation-phoneticTranscription'), ('40', 'speechAnnotation-prosodicAnnotation'), ('41', 'speechAnnotation-soundEvents'), ('44', 'speechAnnotation-soundToTextAlignment'), ('42', 'speechAnnotation-speakerIdentification'), ('43', 'speechAnnotation-speakerTurns'), ('45', 'stemming'), ('46', 'structuralAnnotation'), ('47', 'syntacticAnnotation-shallowParsing'), ('48', 'syntacticAnnotation-subcategorizationFrames'), ('49', 'syntacticAnnotation-treebanks'), ('50', 'syntacticosemanticAnnotation-links'), ('51', 'translation'), ('52', 'transliteration')], default='0', max_length=5, verbose_name='Kind of annotation'),
        ),
    ]