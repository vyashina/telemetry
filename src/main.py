# Copyright (C) 2018-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .backend.backend import BackendRegistry
from .utils import isip
from .utils.sender import TelemetrySender


class SingletonMetaClass(type):
    def __init__(self, cls_name, super_classes, dic):
        self.__single_instance = None
        super().__init__(cls_name, super_classes, dic)

    def __call__(cls, *args, **kwargs):
        if cls.__single_instance is None:
            cls.__single_instance = super(SingletonMetaClass, cls).__call__(*args, **kwargs)
        return cls.__single_instance


class Telemetry(metaclass=SingletonMetaClass):
    """
    The main class to send telemetry data. It uses singleton pattern. The instance should be initialized with the
    application name, version and tracking id just once. Later the instance can be created without parameters.
    """
    def __init__(self, app_name: str = None, app_version: str = None, tid: str = None,
                 backend: [str, None] = 'ga'):
        if app_name is not None:
            self.consent = isip.isip_consent() == isip.ISIPConsent.APPROVED

            if tid is None:
                print('[ WARNING ] Telemetry will not be sent as TID is not specified.')

            self.tid = tid
            self.backend = BackendRegistry.get_backend(backend)(self.tid, app_name, app_version)
            self.sender = TelemetrySender()
        else:  # use already configured instance
            if self.sender is None:
                raise RuntimeError('The first instantiation of the Telemetry should be done with the '
                                   'application name, version and TID.')

    def force_shutdown(self, timeout: float = 1.0):
        """
        Stops currently running threads which may be hanging because of no Internet connection.

        :param timeout: maximum timeout time
        :return: None
        """
        self.sender.force_shutdown(timeout)

    def send_event(self, event_category: str, event_action: str, event_label: str, event_value: int = 1, **kwargs):
        """
        Send single event.

        :param event_category: category of the event
        :param event_action: action of the event
        :param event_label: the label associated with the action
        :param event_value: the integer value corresponding to this label
        :param kwargs: additional parameters
        :return: None
        """
        if self.consent:
            self.sender.send(self.backend, self.backend.build_event_message(event_category, event_action, event_label,
                                                                            event_value, **kwargs))

    def start_session(self, category: str, **kwargs):
        """
        Sends a message about starting of a new session.

        :param kwargs: additional parameters
        :param category: the application code
        :return: None
        """
        if self.consent:
            self.sender.send(self.backend, self.backend.build_session_start_message(category, **kwargs))

    def end_session(self, category: str, **kwargs):
        """
        Sends a message about ending of the current session.

        :param kwargs: additional parameters
        :param category: the application code
        :return: None
        """
        if self.consent:
            self.sender.send(self.backend, self.backend.build_session_end_message(category, **kwargs))

    def send_error(self, category: str, error_msg: str, **kwargs):
        if self.consent:
            self.sender.send(self.backend, self.backend.build_error_message(category, error_msg, **kwargs))

    def send_stack_trace(self, category: str, stack_trace: str, **kwargs):
        if self.consent:
            self.sender.send(self.backend, self.backend.build_stack_trace_message(category, stack_trace, **kwargs))
