# -*- coding: utf-8 -*-
#################################################################################

{
	"name"         : "rightechs Message Wizard",
	"summary"      : """To show messages/warnings in Odoo""",
	"category"     : "Extra Tools",
	"version"      : "1.0.0",
	"sequence"     : 1,
	"author"       : "rightechs Software Pvt. Ltd.",
	"website"      : "https://rightechs-solutions.odoo.com",
	"license"              :  "Other proprietary",
	"description"  : """""",
	"live_test_url": "https://rightechs-solutions.odoo.com",
	"data"         : [
		'security/ir.model.access.csv',
		'wizard/wizard_message.xml'
	],
	"images"       : ['static/description/Banner.png'],
	"installable"  : True,
	"pre_init_hook": "pre_init_check",
}
