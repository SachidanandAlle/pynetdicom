"""
Implementation of the DIMSE service provider.

TODO: rename Send and Receive class methods to lowercase
"""
from io import BytesIO
import logging
import time

from pynetdicom3.dimse_messages import C_STORE_RQ, C_STORE_RSP, \
                                      C_FIND_RQ, C_FIND_RSP, \
                                      C_GET_RQ, C_GET_RSP, \
                                      C_MOVE_RQ, C_MOVE_RSP, \
                                      C_ECHO_RQ, C_ECHO_RSP, \
                                      C_CANCEL_RQ, \
                                      N_EVENT_REPORT_RQ, N_EVENT_REPORT_RSP, \
                                      N_GET_RQ, N_GET_RSP, \
                                      N_SET_RQ, N_SET_RSP, \
                                      N_ACTION_RQ, N_ACTION_RSP, \
                                      N_CREATE_RQ, N_CREATE_RSP, \
                                      N_DELETE_RQ, N_DELETE_RSP, \
                                      DIMSEMessage
from pynetdicom3.dimse_primitives import C_STORE, \
                                        C_FIND, \
                                        C_GET, \
                                        C_MOVE, \
                                        C_ECHO, \
                                        N_EVENT_REPORT, \
                                        N_GET, \
                                        N_SET, \
                                        N_ACTION, \
                                        N_CREATE, \
                                        N_DELETE
from pynetdicom3.primitives import P_DATA

LOGGER = logging.getLogger('pynetdicom3.dimse')


class DIMSEServiceProvider(object):
    """
    PS3.7 6.2
    The DICOM AE uses the services provided by the DICOM Message Service Element
    (DIMSE). DIMSE specifies two sets of services.

    - DIMSE-C supports operations associated with composite SOP Classes and
      provides effective compatibility with the previous versions of the DICOM
      standards.
    - DIMSE-N supports operations associated with normalised SOP Classes and
      provides an extended set of object-orientated operations and notifications

    Service Overview
    ----------------
    The DIMSE service provider supports communication between peer DIMSE service
    users. A service user acts in one of two roles:
    - invoking DIMSE user
    - performing DIMSE user

    Service users make use of service primitives provided by the DIMSE service
    provider. A service primitive shall be one of the following types:
    - request primitive
    - indication primitive
    - response primitive
    - confirmation primitive

    These primitives are used as follows:
    - The invoking service user issues a request primitive to the DIMSE provider
    - The DIMSE provider receives the request primitive and issues an indication
      primitive to the performing service user
    - The performing service user receives the indication primitive and performs
      the requested service
    - The performing service user issues a response primitive to the DIMSE
      provider
    - The DIMSE provider receives the response primitive and issues a
      confirmation primitive to the invoking service user
    - The invoking service user receives the confirmation primitive, completing
      the DIMSE service.

    Service Primitive Classes
    ~~~~~~~~~~~~~~~~~~~~~~~~~
    C_ECHO
    C_STORE
    C_GET
    C_FIND
    C_MOVE
    N_EVENT_REPORT
    N_GET
    N_GET
    N_ACTION
    N_CREATE
    N_DELETE

    Protocol Machine
    ----------------
    PS3.7 8.1
    The DIMSE protocol machine defines the procedures and the encoding rules
    necessary to construct Messages used to exchange command requests and
    responses between peer DIMSE service users.

    The DIMSE protocol machine accepts service user requests and response
    service primitives and constructs Messages defined by the procedures in
    PS3.7 9.3 and 10.3. The DIMSE protocol machine accepts Messages and passes
    them to the DIMSE service user by the means of indication and confirmation
    service primitives.

    Messages
    ~~~~~~~~
    C-STORE: Request/indication    - C_STORE_RQ
             Response/confirmation - C_STORE_RSP
    C-FIND:  Request/indication        - C_FIND_RQ
             Response/confirmation     - C_FIND_RSP
             Cancel request/indication - C_CANCEL_RQ
    C-GET:   Request/indication        - C_GET_RQ
             Response/confirmation     - C_GET_RSP
             Cancel request/indication - C_CANCEL_RQ
    C-MOVE:  Request/indication    - C_MOVE_RQ
             Response/confirmation - C_MOVE_RSP
             Cancel request/indication - C_CANCEL_RQ
    C-ECHO:  Request/indication    - C_ECHO_RQ
             Response/confirmation - C_ECHO_RSP
    N-EVENT-REPORT: Request/indication    - N_EVENT_REPORT_RQ
                    Response/confirmation - N_EVENT_REPORT_RSP
    N-GET:    Request/indication    - N_GET_RQ
              Response/confirmation - N_GET_RSP
    N-SET:    Request/indication    - N_SET_RQ
              Response/confirmation - N_SET_RSP
    N-ACTION: Request/indication    - N_ACTION_RQ
              Response/confirmation - N_ACTION_RSP
    N-CREATE: Request/indication    - N_CREATE_RQ
              Response/confirmation - N_CREATE_RSP
    N-DELETE: Request/indication    - N_DELETE_RQ
              Response/confirmation - N_DELETE_RSP

    Attributes
    ----------
    DUL
    message
    dimse_timeout : int or float or None
        The number of seconds before the DIMSE service timeout. A value of None
        indicates no timeout
    dimse_msg
        ???
    """
    def __init__(self, DUL, dimse_timeout=None):
        self.DUL = DUL
        self.message = None
        self.dimse_timeout = dimse_timeout

    def Send(self, primitive, context_id, max_pdu):
        """
        Send a DIMSE-C or DIMSE-N message to the peer AE

        Parameters
        ----------
        primitive : pynetdicom3.dimse_primitives
            The DIMSE service primitive to send to the peer
        context_id : int
            The ID of the presentation context to be sent under
        max_pdu : int
            The maximum send PDV size acceptable by the peer AE
        """
        if primitive.__class__ == C_ECHO:
            if primitive.MessageID is not None:
                dimse_msg = C_ECHO_RQ()
            else:
                dimse_msg = C_ECHO_RSP()

        elif primitive.__class__ == C_STORE:
            if primitive.MessageID is not None:
                dimse_msg = C_STORE_RQ()
            else:
                dimse_msg = C_STORE_RSP()

        elif primitive.__class__ == C_FIND:
            if primitive.MessageID is not None:
                dimse_msg = C_FIND_RQ()
            elif primitive.Status is not None:
                dimse_msg = C_FIND_RSP()
            else:
                dimse_msg = C_CANCEL_RQ()

        elif primitive.__class__ == C_GET:
            if primitive.MessageID is not None:
                dimse_msg = C_GET_RQ()
            elif primitive.Status is not None:
                dimse_msg = C_GET_RSP()
            else:
                dimse_msg = C_CANCEL_RQ()

        elif primitive.__class__ == C_MOVE:
            if primitive.MessageID is not None:
                dimse_msg = C_MOVE_RQ()
            elif primitive.Status is not None:
                dimse_msg = C_MOVE_RSP()
            else:
                dimse_msg = C_CANCEL_RQ()

        elif primitive.__class__ == N_EVENT_REPORT:
            if primitive.MessageID is not None:
                dimse_msg = N_EVENT_REPORT_RQ()
            else:
                dimse_msg = N_EVENT_REPORT_RSP()

        elif primitive.__class__ == N_GET:
            if primitive.MessageID is not None:
                dimse_msg = N_GET_RQ()
            else:
                dimse_msg = N_GET_RSP()

        elif primitive.__class__ == N_SET:
            if primitive.MessageID is not None:
                dimse_msg = N_SET_RQ()
            else:
                dimse_msg = N_SET_RSP()

        elif primitive.__class__ == N_ACTION:
            if primitive.MessageID is not None:
                dimse_msg = N_ACTION_RQ()
            else:
                dimse_msg = N_ACTION_RSP()

        elif primitive.__class__ == N_CREATE:
            if primitive.MessageID is not None:
                dimse_msg = N_CREATE_RQ()
            else:
                dimse_msg = N_CREATE_RSP()

        elif primitive.__class__ == N_DELETE:
            if primitive.MessageID is not None:
                dimse_msg = N_DELETE_RQ()
            else:
                dimse_msg = N_DELETE_RSP()

        # Convert DIMSE primitive to DIMSE Message
        dimse_msg.primitive_to_message(primitive)

        # Callbacks
        self.on_send_dimse_message(dimse_msg)

        # Split the full messages into P-DATA chunks,
        #   each below the max_pdu size
        pdvs = dimse_msg.Encode(context_id, max_pdu)

        # Send each of the P-DATA to the peer via the DUL provider
        for pp in pdvs:
            self.DUL.send_pdu(pp)

    def Receive(self, wait=False, dimse_timeout=None):
        """
        Set the DIMSE provider in a mode ready to receive a response from the
        peer

        Parameters
        ----------
        wait : bool, optional
            Wait until a response has been received (default: False)
        dimse_timeout : int, optional
            Wait `dimse_timeout` seconds for a response (default: no timeout)

        Returns
        -------
        pynetdicom3.DIMSEmessage.DIMSEMessage, int or None, None
            Returns the complete DIMSE message and its presentation context ID
            or None, None if
        """
        dimse_timeout = self.dimse_timeout

        if self.message is None:
            self.message = DIMSEMessage()

        if wait:
            # Loop until complete DIMSE message is received
            #   message may be split into 1 or more fragments
            while True:
                time.sleep(0.001)

                nxt = self.DUL.peek_next_pdu()
                if nxt is None:
                    continue

                if nxt.__class__ is not P_DATA:
                    return None, None

                msg = self.DUL.receive_pdu(wait, dimse_timeout)

                if self.message.Decode(msg):
                    # Callback
                    self.on_receive_dimse_message(self.message)

                    context_id = self.message.ID
                    primitive = self.message.message_to_primitive()

                    # Fix for memory leak, Issue #41
                    #   Reset the DIMSEMessage, ready for the next message
                    self.message.encoded_command_set = BytesIO()
                    self.message.data_set = BytesIO()
                    self.message = None

                    return primitive, context_id
                else:
                    return None, None

        else:
            cls = self.DUL.peek_next_pdu().__class__
            if cls not in (type(None), P_DATA):
                return None, None

            primitive = self.DUL.receive_pdu(wait, dimse_timeout)

            if self.message.Decode(primitive):
                # Callback
                self.on_receive_dimse_message(self.message)

                dimse_msg = self.message

                context_id = dimse_msg.ID
                dimse_msg = dimse_msg.message_to_primitive()

                # Fix for memory leak, Issue #41
                #   Reset the DIMSEMessage, ready for the next message
                self.message.encoded_command_set = BytesIO()
                self.message.data_set = BytesIO()
                self.dimse_msg = None

                return dimse_msg, context_id
            else:
                return None, None


    # Debugging and AE callbacks
    def on_send_dimse_message(self, message):
        """
        Placeholder for a function callback. Function will be called
        immediately prior to encoding and sending a DIMSE message

        Parameters
        ----------
        message - pynetdicom3.DIMSEmessage.DIMSEMessage
            The DIMSE message to be sent
        """
        callback = {C_ECHO_RQ  : self.debug_send_c_echo_rq,
                    C_ECHO_RSP : self.debug_send_c_echo_rsp,
                    C_FIND_RQ  : self.debug_send_c_find_rq,
                    C_FIND_RSP : self.debug_send_c_find_rsp,
                    C_CANCEL_RQ : self.debug_send_c_cancel_rq,
                    C_GET_RQ  : self.debug_send_c_get_rq,
                    C_GET_RSP : self.debug_send_c_get_rsp,
                    C_MOVE_RQ  : self.debug_send_c_move_rq,
                    C_MOVE_RSP : self.debug_send_c_move_rsp,
                    C_STORE_RQ  : self.debug_send_c_store_rq,
                    C_STORE_RSP : self.debug_send_c_store_rsp,
                    N_EVENT_REPORT_RQ  : self.debug_send_n_event_report_rq,
                    N_EVENT_REPORT_RSP : self.debug_send_n_event_report_rsp,
                    N_SET_RQ  : self.debug_send_n_set_rq,
                    N_SET_RSP : self.debug_send_n_set_rsp,
                    N_GET_RQ  : self.debug_send_n_get_rq,
                    N_GET_RSP : self.debug_send_n_get_rsp,
                    N_ACTION_RQ  : self.debug_send_n_action_rq,
                    N_ACTION_RSP : self.debug_send_n_action_rsp,
                    N_CREATE_RQ  : self.debug_send_n_create_rq,
                    N_CREATE_RSP : self.debug_send_n_create_rsp,
                    N_DELETE_RQ  : self.debug_send_n_delete_rq,
                    N_DELETE_RSP : self.debug_send_n_delete_rsp}

        callback[type(message)](message)

    def on_receive_dimse_message(self, message):
        """
        Placeholder for a function callback. Function will be called
        immediately after receiving and decoding a DIMSE message

        Parameters
        ----------
        sop_class - pynetdicom3.sop_class.SOPClass
            A SOP Class instance of the type referred to by the message
        message - pydicom.Dataset
            The DIMSE message that was received as a Dataset
        """
        callback = {C_ECHO_RQ  : self.debug_receive_c_echo_rq,
                    C_ECHO_RSP : self.debug_receive_c_echo_rsp,
                    C_FIND_RQ  : self.debug_receive_c_find_rq,
                    C_FIND_RSP : self.debug_receive_c_find_rsp,
                    C_CANCEL_RQ : self.debug_receive_c_cancel_rq,
                    C_GET_RQ  : self.debug_receive_c_get_rq,
                    C_GET_RSP : self.debug_receive_c_get_rsp,
                    C_MOVE_RQ  : self.debug_receive_c_move_rq,
                    C_MOVE_RSP : self.debug_receive_c_move_rsp,
                    C_STORE_RQ  : self.debug_receive_c_store_rq,
                    C_STORE_RSP : self.debug_receive_c_store_rsp,
                    N_EVENT_REPORT_RQ  : self.debug_receive_n_event_report_rq,
                    N_EVENT_REPORT_RSP : self.debug_receive_n_event_report_rsp,
                    N_SET_RQ  : self.debug_receive_n_set_rq,
                    N_SET_RSP : self.debug_receive_n_set_rsp,
                    N_GET_RQ  : self.debug_receive_n_get_rq,
                    N_GET_RSP : self.debug_receive_n_get_rsp,
                    N_ACTION_RQ  : self.debug_receive_n_action_rq,
                    N_ACTION_RSP : self.debug_receive_n_action_rsp,
                    N_CREATE_RQ  : self.debug_receive_n_create_rq,
                    N_CREATE_RSP : self.debug_receive_n_create_rsp,
                    N_DELETE_RQ  : self.debug_receive_n_delete_rq,
                    N_DELETE_RSP : self.debug_receive_n_delete_rsp}

        callback[type(message)](message)


    # Mid-level DIMSE related logging/debugging
    @staticmethod
    def debug_send_c_echo_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_ECHO_RQ
            The C-ECHO-RQ DIMSE Message to be sent
        """
        ds = dimse_msg.command_set
        LOGGER.info("Sending Echo Request: MsgID %s", ds.MessageID)

    @staticmethod
    def debug_send_c_echo_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_ECHO_RSP
            The C-ECHO-RSP DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_c_store_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_STORE_RQ
            The C-STORE-RQ DIMSE Message to be sent
        """
        ds = dimse_msg.command_set

        priority_str = {2 : 'Low',
                        0 : 'Medium',
                        1 : 'High'}
        priority = priority_str[ds.Priority]

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        if ds.AffectedSOPClassUID.name == 'CT Image Storage':
            dataset_type = ', (CT)'
        elif ds.AffectedSOPClassUID.name == 'MR Image Storage':
            dataset_type = ', (MR)'
        else:
            dataset_type = ''

        LOGGER.info("Sending Store Request: MsgID %s%s",
                    ds.MessageID, dataset_type)

        s = []
        s.append('===================== OUTGOING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-STORE RQ'))
        s.append('Message ID                    : {0!s}'.format(ds.MessageID))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Affected SOP Instance UID     : {0!s}'
                 .format(ds.AffectedSOPInstanceUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('Priority                      : {0!s}'.format(priority))
        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')
        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_send_c_store_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_STORE_RSP
            The C-STORE-RSP DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_c_find_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_FIND_RQ
            The C-FIND-RQ DIMSE Message to be sent
        """
        ds = dimse_msg.command_set

        priority_str = {2 : 'Low',
                        0 : 'Medium',
                        1 : 'High'}
        priority = priority_str[ds.Priority]

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'
        
        LOGGER.info("Sending Get Request: MsgID %s%s", ds.MessageID)

        s = []
        s.append('===================== OUTGOING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-FIND RQ'))
        s.append('Presentation Context ID       : {0!s}'.format(dimse_msg.ID))
        s.append('Message ID                    : {0!s}'.format(ds.MessageID))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('Priority                      : {0!s}'.format(priority))
        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_send_c_find_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_FIND_RSP
            The sent C-FIND-RSP DIMSE Message
        """
        ds = dimse_msg.command_set

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        s = []
        s.append('===================== OUTGOING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-FIND RSP'))
        s.append('Message ID Being Responded To : {0!s}'
                 .format(ds.MessageIDBeingRespondedTo))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('DIMSE Status                  : 0x{0:04x}'.format(ds.Status))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_send_c_cancel_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_CANCEL_RQ
            The C-CANCEL-FIND-RQ, C-CANCEL-GET-RQ or C-CANCEL-MOVE-RQ DIMSE
            Message to be sent
        """
        pass

    @staticmethod
    def debug_send_c_get_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_GET_RQ
            The C-GET-RQ DIMSE Message to be sent
        """
        cs = dimse_msg.command_set

        priority_str = {2 : 'Low',
                        0 : 'Medium',
                        1 : 'High'}
        priority = priority_str[cs.Priority]

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        LOGGER.info("Sending Get Request: MsgID %s", cs.MessageID)

        s = []
        s.append('===================== OUTGOING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-GET RQ'))
        s.append('Message ID                    : {0!s}'.format(cs.MessageID))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(cs.AffectedSOPClassUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('Priority                      : {0!s}'.format(priority))
        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')
        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_send_c_get_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_GET_RSP
            The sent C-GET-RSP DIMSE Message
        """
        ds = dimse_msg.command_set

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        s = []
        s.append('===================== OUTGOING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-GET RSP'))
        s.append('Message ID Being Responded To : {0!s}'
                 .format(ds.MessageIDBeingRespondedTo))
        s.append('Affected SOP Class UID        : none')
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('DIMSE Status                  : 0x{0:04x}'.format(ds.Status))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_send_c_move_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_MOVE_RQ
            The C-MOVE-RQ DIMSE Message to be sent
        """
        ds = dimse_msg.command_set

        priority_str = {2 : 'Low',
                        0 : 'Medium',
                        1 : 'High'}
        priority = priority_str[ds.Priority]

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        LOGGER.info("Sending Move Request: MsgID %s", ds.MessageID)

        s = []
        s.append('===================== OUTGOING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-MOVE RQ'))
        s.append('Message ID                    : {0!s}'.format(ds.MessageID))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Move Destination              : {0!s}'
                 .format(ds.MoveDestination.decode('utf-8')))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('Priority                      : {0!s}'.format(priority))
        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')
        for line in s:
            LOGGER.debug(line)
        return None

    @staticmethod
    def debug_send_c_move_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.dimse_messages.C_MOVE_RSP
            The C-MOVE-RSP DIMSE Message to be sent
        """
        ds = dimse_msg.command_set

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        s = []
        s.append('===================== OUTGOING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-MOVE RSP'))
        s.append('Message ID Being Responded To : {0!s}'
                                        .format(ds.MessageIDBeingRespondedTo))
        if 'AffectedSOPClass' in ds:
            s.append('Affected SOP Class UID        : {0!s}'
                                        .format(ds.AffectedSOPClassUID))
        else:
            s.append('Affected SOP Class UID        : none')
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('DIMSE Status                  : 0x{0:04x}'.format(ds.Status))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_receive_c_echo_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_ECHO_RQ
            The received C-ECHO-RQ DIMSE Message
        """
        ds = dimse_msg.command_set

        LOGGER.info('Received Echo Request (MsgID %s)', ds.MessageID)

        s = []
        s.append('===================== INCOMING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-ECHO RQ'))
        s.append('Presentation Context ID       : {0!s}'.format(dimse_msg.ID))
        s.append('Message ID                    : {0!s}'.format(ds.MessageID))
        s.append('Data Set                      : {0!s}'.format('none'))
        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_receive_c_echo_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_ECHO_RSP
            The received C-ECHO-RSP DIMSE Message
        """
        # Status must always be Success for C_ECHO_RSP
        LOGGER.info("Received Echo Response (Status: Success)")

    @staticmethod
    def debug_receive_c_store_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_STORE_RQ
            The received C-STORE-RQ DIMSE Message
        """
        ds = dimse_msg.command_set

        priority_str = {2 : 'Low',
                        0 : 'Medium',
                        1 : 'High'}
        priority = priority_str[ds.Priority]

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        LOGGER.info('Received Store Request')

        s = []
        s.append('===================== INCOMING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-STORE RQ'))
        s.append('Presentation Context ID       : {0!s}'.format(dimse_msg.ID))
        s.append('Message ID                    : {0!s}'.format(ds.MessageID))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Affected SOP Instance UID     : {0!s}'
                 .format(ds.AffectedSOPInstanceUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('Priority                      : {0!s}'.format(priority))
        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')
        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_receive_c_store_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_STORE_RSP
            The received C-STORE-RSP DIMSE Message
        """
        ds = dimse_msg.command_set

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        # See PS3.4 Annex B.2.3 for Storage Service Class Statuses
        status = '0x{0:04x}'.format(ds.Status)
        if status == '0x0000':
            status += ': Success'
        elif '0xb000' in status:
            status += ': Warning - Coercion of data elements'
        elif '0xb007' in status:
            status += ': Warning - Dataset does not match SOP Class'
        elif '0xb006' in status:
            status += ': Warning - Elements discarded'
        elif ds.Status in range(0xA700, 0xA7FF + 1):
            status += ': Failure - Out of resources'
        elif ds.Status in range(0xA900, 0xA9FF + 1):
            status += ': Failure - Dataset does not match SOP Class'
        elif ds.Status in range(0xC000, 0xCFFF + 1):
            status += ': Failure - Cannot understand'

        LOGGER.info('Received Store Response')
        s = []
        s.append('===================== INCOMING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-STORE RSP'))
        s.append('Presentation Context ID       : {0!s}'.format(dimse_msg.ID))
        s.append('Message ID Being Responded To : {0!s}'
                 .format(ds.MessageIDBeingRespondedTo))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Affected SOP Instance UID     : {0!s}'
                 .format(ds.AffectedSOPInstanceUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('DIMSE Status                  : {0!s}'.format(status))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_receive_c_find_rq(dimse_msg):
        """
        Called on receiving a C-FIND-RQ from the peer AE.
        The C-FIND service is used by a DIMSE to match a set of Attributes
        against the Attributes of a set of composite SOP
        Instances maintained by a peer DIMSE user.

        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_FIND_RQ
            The received C-FIND-RQ DIMSE Message
        """
        ds = dimse_msg.command_set

        priority_str = {2 : 'Low',
                        0 : 'Medium',
                        1 : 'High'}
        priority = priority_str[ds.Priority]

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        s = []
        s.append('===================== INCOMING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-FIND RQ'))
        s.append('Message ID                    : {0!s}'.format(ds.MessageID))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('Priority                      : {0!s}'.format(priority))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.info(line)

    @staticmethod
    def debug_receive_c_find_rsp(dimse_msg):
        """
        Called on receiving a C-FIND-RSP from the peer AE.
        The C-FIND service is used by a DIMSE to match a set of Attributes
        against the Attributes of a set of composite SOP
        Instances maintained by a peer DIMSE user.

        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_FIND_RSP
            The received C-FIND-RSP DIMSE Message
        """
        ds = dimse_msg.command_set
        if ds.Status != 0x0000:
            return

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        s = []
        s.append('===================== INCOMING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-FIND RSP'))
        s.append('Message ID Being Responded To : {0!s}'
                 .format(ds.MessageIDBeingRespondedTo))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('DIMSE Status                  : 0x{0:04x}'.format(ds.Status))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.info(line)

    @staticmethod
    def debug_receive_c_cancel_rq(dimse_msg):
        """
        Placeholder for C-CANCEL-FIND-RQ, C-CANCEL-GET-RQ and C-CANCEL-MOVE-RQ

        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_CANCEL_RQ
            The received C-CANCEL-RQ DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_c_get_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_GET_RQ
            The received C-GET-RQ DIMSE Message
        """
        ds = dimse_msg.command_set

        priority_str = {2 : 'Low',
                        0 : 'Medium',
                        1 : 'High'}
        priority = priority_str[ds.Priority]

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        s = []
        s.append('===================== INCOMING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-GET RQ'))
        s.append('Message ID                    : {0!s}'.format(ds.MessageID))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('Priority                      : {0!s}'.format(priority))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.info(line)

    @staticmethod
    def debug_receive_c_get_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_GET_RSP
            The received C-GET-RSP DIMSE Message
        """
        ds = dimse_msg.command_set

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        s = []
        s.append('===================== INCOMING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-GET RSP'))
        s.append('Presentation Context ID       : {0!s}'.format(dimse_msg.ID))
        s.append('Message ID Being Responded To : {0!s}'
                 .format(ds.MessageIDBeingRespondedTo))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        if 'NumberOfRemainingSuboperations' in ds:
            s.append('Remaining Sub-operations      : {0!s}'
                     .format(ds.NumberOfRemainingSuboperations))
        if 'NumberOfCompletedSuboperations' in ds:
            s.append('Completed Sub-operations      : {0!s}'
                     .format(ds.NumberOfCompletedSuboperations))
        if 'NumberOfFailedSuboperations' in ds:
            s.append('Failed Sub-operations         : {0!s}'
                     .format(ds.NumberOfFailedSuboperations))
        if 'NumberOfWarningSuboperations' in ds:
            s.append('Warning Sub-operations        : {0!s}'
                     .format(ds.NumberOfWarningSuboperations))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('DIMSE Status                  : 0x{0:04x}'.format(ds.Status))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_receive_c_move_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_MOVE_RQ
            The received C-MOVE-RQ DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_c_move_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.C_MOVE_RSP
            The received C-MOVE-RSP DIMSE Message
        """
        ds = dimse_msg.command_set

        dataset = 'None'
        if dimse_msg.data_set.getvalue() != b'':
            dataset = 'Present'

        s = []
        s.append('===================== INCOMING DIMSE MESSAGE ================'
                 '====')
        s.append('Message Type                  : {0!s}'.format('C-MOVE RSP'))
        s.append('Message ID Being Responded To : {0!s}'
                 .format(ds.MessageIDBeingRespondedTo))
        s.append('Affected SOP Class UID        : {0!s}'
                 .format(ds.AffectedSOPClassUID))
        if 'NumberOfRemainingSuboperations' in ds:
            s.append('Remaining Sub-operations      : {0!s}'
                     .format(ds.NumberOfRemainingSuboperations))
        if 'NumberOfCompletedSuboperations' in ds:
            s.append('Completed Sub-operations      : {0!s}'
                     .format(ds.NumberOfCompletedSuboperations))
        if 'NumberOfFailedSuboperations' in ds:
            s.append('Failed Sub-operations         : {0!s}'
                     .format(ds.NumberOfFailedSuboperations))
        if 'NumberOfWarningSuboperations' in ds:
            s.append('Warning Sub-operations        : {0!s}'
                     .format(ds.NumberOfWarningSuboperations))
        s.append('Data Set                      : {0!s}'.format(dataset))
        s.append('DIMSE Status                  : 0x{0:04x}'.format(ds.Status))

        s.append('======================= END DIMSE MESSAGE ==================='
                 '====')

        for line in s:
            LOGGER.debug(line)

    @staticmethod
    def debug_send_n_event_report_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_EVENT_REPORT_RQ
            The N-EVENT-REPORT-RQ DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_event_report_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_EVENT_REPORT_RSP
            The N-EVENT-REPORT-RSP DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_get_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_GET_RQ
            The N-GET-RQ DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_get_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_GET_RSP
            The N-GET-RSP DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_set_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_SET_RQ
            The N-SET-RQ DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_set_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_SET_RSP
            The N-SET-RSP DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_action_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_ACTION_RQ
            The N-ACTION-RQ DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_action_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_ACTION_RSP
            The N-ACTION-RSP DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_create_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_CREATE_RQ
            The N-CREATE-RQ DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_create_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_CREATE_RSP
            The N-CREATE-RSP DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_delete_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_DELETE_RQ
            The N-DELETE-RQ DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_send_n_delete_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_DELETE_RSP
            The N-DELETE-RSP DIMSE Message to be sent
        """
        pass

    @staticmethod
    def debug_receive_n_event_report_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_EVENT_REPORT_RQ
            The received N-EVENT-REPORT-RQ DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_event_report_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_EVENT_REPORT_RSP
            The received N-EVENT-REPORT-RSP DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_get_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_GET_RQ
            The received N-GET-RQ DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_get_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_GET_RSP
            The received N-GET-RSP DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_set_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_SET_RQ
            The received N-SET-RQ DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_set_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_SET_RSP
            The received N-SET-RSP DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_action_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_ACTION_RQ
            The received N-ACTION-RQ DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_action_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_ACTION_RSP
            The received N-ACTION-RSP DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_create_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_CREATE_RQ
            The received N-CREATE-RQ DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_create_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_CREATE_RSP
            The received N-CREATE-RSP DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_delete_rq(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_DELETE_RQ
            The received N-DELETE-RQ DIMSE Message
        """
        pass

    @staticmethod
    def debug_receive_n_delete_rsp(dimse_msg):
        """
        Parameters
        ----------
        dimse_msg : pynetdicom3.DIMSEmessage.N_DELETE_RSP
            The received N-DELETE-RSP DIMSE Message
        """
        pass
