# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-18 15:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0007_auto_20160618_1729'),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Sorry, no help available for provenance.geographic.place', max_length=80, verbose_name='Place (city)')),
            ],
        ),
        migrations.AlterField(
            model_name='geographicprovenance',
            name='country',
            field=models.CharField(choices=[('1', 'Afghanistan'), ('3', 'Albania'), ('4', 'Algeria'), ('5', 'American Samoa'), ('6', 'Andorra'), ('7', 'Angola'), ('8', 'Anguilla'), ('9', 'Antarctica'), ('10', 'Antigua and Barbuda'), ('11', 'Argentina'), ('12', 'Armenia'), ('13', 'Aruba'), ('14', 'Australia'), ('15', 'Austria'), ('16', 'Azerbaijan'), ('17', 'Bahamas'), ('18', 'Bahrain'), ('19', 'Bangladesh'), ('20', 'Barbados'), ('21', 'Belarus'), ('22', 'Belgium'), ('23', 'Belize'), ('24', 'Benin'), ('25', 'Bermuda'), ('26', 'Bhutan'), ('27', 'Bolivia (Plurinational State of)'), ('28', 'Bonaire, Sint Eustatius and Saba'), ('29', 'Bosnia and Herzegovina'), ('30', 'Botswana'), ('31', 'Bouvet Island'), ('32', 'Brazil'), ('33', 'British Indian Ocean Territory'), ('34', 'Brunei Darussalam'), ('35', 'Bulgaria'), ('36', 'Burkina Faso'), ('37', 'Burundi'), ('38', 'Cabo Verde'), ('39', 'Cambodia'), ('40', 'Cameroon'), ('41', 'Canada'), ('42', 'Cayman Islands'), ('43', 'Central African Republic'), ('44', 'Chad'), ('45', 'Chile'), ('46', 'China'), ('47', 'Christmas Island'), ('48', 'Cocos (Keeling) Islands'), ('49', 'Colombia'), ('50', 'Comoros'), ('51', 'Congo'), ('52', 'Congo (Democratic Republic of the)'), ('53', 'Cook Islands'), ('54', 'Costa Rica'), ('56', 'Croatia'), ('57', 'Cuba'), ('58', 'Curaçao'), ('59', 'Cyprus'), ('60', 'Czech Republic'), ('55', "Côte d'Ivoire"), ('61', 'Denmark'), ('62', 'Djibouti'), ('63', 'Dominica'), ('64', 'Dominican Republic'), ('65', 'Ecuador'), ('66', 'Egypt'), ('67', 'El Salvador'), ('68', 'Equatorial Guinea'), ('69', 'Eritrea'), ('70', 'Estonia'), ('71', 'Ethiopia'), ('72', 'Falkland Islands (Malvinas)'), ('73', 'Faroe Islands'), ('74', 'Fiji'), ('75', 'Finland'), ('76', 'France'), ('77', 'French Guiana'), ('78', 'French Polynesia'), ('79', 'French Southern Territories'), ('80', 'Gabon'), ('81', 'Gambia'), ('82', 'Georgia'), ('83', 'Germany'), ('84', 'Ghana'), ('85', 'Gibraltar'), ('86', 'Greece'), ('87', 'Greenland'), ('88', 'Grenada'), ('89', 'Guadeloupe'), ('90', 'Guam'), ('91', 'Guatemala'), ('92', 'Guernsey'), ('93', 'Guinea'), ('94', 'Guinea-Bissau'), ('95', 'Guyana'), ('96', 'Haiti'), ('97', 'Heard Island and McDonald Islands'), ('98', 'Holy See'), ('99', 'Honduras'), ('100', 'Hong Kong'), ('101', 'Hungary'), ('102', 'Iceland'), ('103', 'India'), ('104', 'Indonesia'), ('105', 'Iran (Islamic Republic of)'), ('106', 'Iraq'), ('107', 'Ireland'), ('108', 'Ireland'), ('109', 'Isle of Man'), ('110', 'Israel'), ('111', 'Italy'), ('112', 'Jamaica'), ('113', 'Japan'), ('114', 'Jersey'), ('115', 'Jordan'), ('116', 'Kazakhstan'), ('117', 'Kenya'), ('118', 'Kiribati'), ('119', "Korea (Democratic People's Republic of)"), ('120', 'Korea (Republic of)'), ('121', 'Kuwait'), ('122', 'Kyrgyzstan'), ('123', "Lao People's Democratic Republic"), ('124', 'Latvia'), ('125', 'Lebanon'), ('126', 'Lesotho'), ('127', 'Liberia'), ('128', 'Libya'), ('129', 'Liechtenstein'), ('130', 'Lithuania'), ('131', 'Luxembourg'), ('132', 'Macao'), ('133', 'Macedonia (the former Yugoslav Republic of)'), ('134', 'Madagascar'), ('135', 'Malawi'), ('136', 'Malaysia'), ('137', 'Maldives'), ('138', 'Mali'), ('139', 'Malta'), ('140', 'Marshall Islands'), ('141', 'Martinique'), ('142', 'Mauritania'), ('143', 'Mauritius'), ('144', 'Mayotte'), ('145', 'Mexico'), ('146', 'Micronesia (Federated States of)'), ('147', 'Moldova (Republic of)'), ('148', 'Monaco'), ('149', 'Mongolia'), ('150', 'Montenegro'), ('151', 'Montserrat'), ('152', 'Morocco'), ('153', 'Mozambique'), ('154', 'Myanmar'), ('155', 'Namibia'), ('156', 'Nauru'), ('157', 'Nepal'), ('158', 'Netherlands'), ('159', 'New Caledonia'), ('160', 'New Zealand'), ('161', 'Nicaragua'), ('162', 'Niger'), ('163', 'Nigeria'), ('164', 'Niue'), ('165', 'Norfolk Island'), ('166', 'Northern Mariana Islands'), ('167', 'Norway'), ('168', 'Oman'), ('170', 'Pakistan'), ('171', 'Palau'), ('172', 'Palestine, State of'), ('173', 'Panama'), ('174', 'Papua New Guinea'), ('175', 'Paraguay'), ('176', 'Peru'), ('177', 'Philippines'), ('178', 'Pitcairn'), ('179', 'Poland'), ('180', 'Portugal'), ('181', 'Puerto Rico'), ('182', 'Qatar'), ('184', 'Romania'), ('185', 'Russian Federation'), ('186', 'Rwanda'), ('183', 'Réunion'), ('187', 'Saint Barthélemy'), ('188', 'Saint Helena, Ascension and Tristan da Cunha'), ('189', 'Saint Kitts and Nevis'), ('190', 'Saint Lucia'), ('191', 'Saint Martin (French part)'), ('192', 'Saint Pierre and Miquelon'), ('193', 'Saint Vincent and the Grenadines'), ('194', 'Samoa'), ('195', 'San Marino'), ('196', 'Sao Tome and Principe'), ('197', 'Saudi Arabia'), ('198', 'Senegal'), ('199', 'Serbia'), ('200', 'Seychelles'), ('201', 'Sierra Leone'), ('202', 'Singapore'), ('203', 'Sint Maarten (Dutch part)'), ('204', 'Slovakia'), ('205', 'Slovenia'), ('206', 'Solomon Islands'), ('207', 'Somalia'), ('208', 'South Africa'), ('209', 'South Georgia and the South Sandwich Islands'), ('210', 'South Sudan'), ('211', 'Spain'), ('212', 'Sri Lanka'), ('213', 'Sudan'), ('214', 'Suriname'), ('215', 'Svalbard and Jan Mayen'), ('216', 'Swaziland'), ('217', 'Sweden'), ('218', 'Switzerland'), ('219', 'Syrian Arab Republic'), ('220', 'Taiwan, Province of China[a]'), ('221', 'Tajikistan'), ('222', 'Tanzania, United Republic of'), ('223', 'Thailand'), ('224', 'Timor-Leste'), ('225', 'Togo'), ('226', 'Tokelau'), ('227', 'Tonga'), ('228', 'Trinidad and Tobago'), ('229', 'Tunisia'), ('230', 'Turkey'), ('231', 'Turkmenistan'), ('232', 'Turks and Caicos Islands'), ('233', 'Tuvalu'), ('234', 'Uganda'), ('235', 'Ukraine'), ('236', 'United Arab Emirates'), ('237', 'United Kingdom of Great Britain and Northern '), ('238', 'United States Minor Outlying Islands'), ('239', 'United States of America'), ('240', 'Uruguay'), ('241', 'Uzbekistan'), ('242', 'Vanuatu'), ('243', 'Venezuela (Bolivarian Republic of)'), ('244', 'Viet Nam'), ('245', 'Virgin Islands (British)'), ('246', 'Virgin Islands (U.S.)'), ('247', 'Wallis and Futuna'), ('248', 'Western Sahara'), ('249', 'Yemen'), ('250', 'Zambia'), ('251', 'Zimbabwe'), ('169', 'other'), ('252', 'unknown'), ('2', 'Åland Islands')], default='0', help_text='Sorry, no help available for country.name', max_length=5, verbose_name='Country included in this geographic coverage'),
        ),
        migrations.RemoveField(
            model_name='geographicprovenance',
            name='place',
        ),
        migrations.AddField(
            model_name='geographicprovenance',
            name='place',
            field=models.ManyToManyField(blank=True, to='collection.City'),
        ),
    ]