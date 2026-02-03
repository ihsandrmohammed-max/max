# -*- coding: utf-8 -*-

from . import models
from . import wizard
from . import controllers
from . import tools

from logging import getLogger
_logger = getLogger(__name__)

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if not 17.0 < float(server_serie) <= 18.0:
        raise UserError(f'Module support Odoo series 18.0 but found {server_serie}.')
