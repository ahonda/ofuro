#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ryu.controller.event import EventBase


class SwitchEventBase(EventBase):

    def __init__(self, switch):
        super(SwitchEventBase, self).__init__()
        self.switch = switch


class AddSwitchEvent(SwitchEventBase):
    pass


class UpdateSwitchEvent(SwitchEventBase):
    pass


class LeaveSwitchEvent(SwitchEventBase):
    pass
