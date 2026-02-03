# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


class OdooSallaConnector(http.Controller):
	@http.route('/salla/authenticate', type='http', auth='public')
	def odoo_salla_connector(self, *args, **kwargs):
		return_key, instance_id = kwargs.get('state') , False
		multichannel = request.env['multi.channel.sale']
		if return_key:
			try:
				connection = multichannel.search([('salla_verification_key','=',return_key)], limit=1)
				if not connection:
					_logger.error(f"Authentication Failed, there is no multichannel instance with verification key: '{return_key}' in your odoo")
				else:
					instance_id = connection.id
					if kwargs.get('error'):
						connection.write({'state': 'error'})
						_logger.error('Error: %r', kwargs)
					else:
						if not connection.create_salla_connection(kwargs):
							connection.write({'state': 'error'})
			except Exception as e:
				_logger.error("Error Found While Generating Access Token %r", str(e))
		return request.redirect(multichannel.redirect_to_channel(instance_id))
