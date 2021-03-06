#
# soaplib - Copyright (C) 2009 Aaron Bickell, Jamie Kirkpatrick
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#

import cStringIO
import traceback

from swissdock_ws.soaplib.soap import (make_soap_envelope, make_soap_fault, from_soap,
    collapse_swa, apply_mtom)
from swissdock_ws.soaplib.service import SoapServiceBase
from swissdock_ws.soaplib.util import reconstruct_url
from swissdock_ws.soaplib.serializers.primitive import string_encoding, Fault
from swissdock_ws.soaplib.etimport import ElementTree
from threading import local

request = local()

_exceptions = False
_exception_logger = None

_debug = False
_debug_logger = None

###################################################################
# Logging / Debugging Utilities                                   #
# replace with python logger?                                     #
###################################################################


def _dump(e): # util?
    print e


def log_exceptions(on, out=_dump):
    global _exceptions
    global _exception_logger

    _exceptions=on
    _exception_logger=out


def log_debug(on, out=_dump):
    global _debug
    global _debug_logger
    _debug=on
    _debug_logger=out


def debug(msg):
    global _debug
    global _debug_logger
    if _debug:
        _debug_logger(msg)


def exceptions(msg):
    global _exceptions
    global _exception_logger
    if _exceptions:
        _exception_logger(msg)


def reset_request():
    '''
    This method clears the data stored in the threadlocal
    request object
    '''
    request.environ = None
    request.header = None
    request.additional = {}


class WSGISoapApp(object):
    '''
    This is the base object representing a soap web application, and conforms
    to the WSGI specification (PEP 333).  This object should be overridden
    and getHandler(environ) overridden to provide the object implementing
    the specified functionality.  Hooks have been added so that the subclass
    can react to various events that happen durring the execution of the
    request.
    '''

    def onCall(self, environ):
        '''
        This is the first method called when this WSGI app is invoked
        @param the wsgi environment
        '''
        pass

    def onWsdl(self, environ, wsdl):
        '''
        This is called when a wsdl is requested
        @param the wsgi environment
        @param the wsdl string
        '''
        pass

    def onWsdlException(self, environ, exc, resp):
        '''
        Called when an exception occurs durring wsdl generation
        @param the wsgi environment
        @param exc the exception
        @param the fault response string
        '''
        pass

    def onMethodExec(self, environ, body, py_params, soap_params):
        '''
        Called BEFORE the service implementing the functionality is called
        @param the wsgi environment
        @param the body element of the soap request
        @param the tuple of python params being passed to the method
        @param the soap elements for each params
        '''
        pass

    def onResults(self, environ, py_results, soap_results):
        '''
        Called AFTER the service implementing the functionality is called
        @param the wsgi environment
        @param the python results from the method
        @param the xml serialized results of the method
        '''
        pass

    def onException(self, environ, exc, resp):
        '''
        Called when an error occurs durring execution
        @param the wsgi environment
        @param the exception
        @param the response string
        '''
        pass

    def onReturn(self, environ, returnString):
        '''
        Called before the application returns
        @param the wsgi environment
        @param return string of the soap request
        '''
        pass

    def getHandler(self, environ):
        '''
        This method returns the object responsible for processing a given
        request, and needs to be overridden by a subclass to handle
        the application specific  mapping of the request to the appropriate
        handler.
        @param the wsgi environment
        @returns the object to be called for the soap operation
        '''
        raise Exception("Not implemented")

    def __call__(self, environ, start_response, address_url=None):
        '''
        This method conforms to the WSGI spec for callable wsgi applications
        (PEP 333). It looks in environ['wsgi.input'] for a fully formed soap
        request envelope, will deserialize the request parameters and call the
        method on the object returned by the getHandler() method.
        @param the http environment
        @param a callable that begins the response message
        @returns the string representation of the soap call
        '''
        methodname = ''
        try:
            reset_request()
            request.environ = environ

            # implementation hook
            self.onCall(environ)

            serviceName = environ['PATH_INFO'].split('/')[-1]
            service = self.getHandler(environ)
            if ((environ['QUERY_STRING'].endswith('wsdl') or
                 environ['PATH_INFO'].endswith('wsdl')) and
                environ['REQUEST_METHOD'].lower() == 'get'):
                # get the wsdl for the service
                #
                # Assume path_info matches pattern
                # /stuff/stuff/stuff/serviceName.wsdl or ?WSDL
                #
                serviceName = serviceName.split('.')[0]
                if address_url:
                    url = address_url
                else:
                    url = reconstruct_url(environ).split('.wsdl')[0]

                start_response('200 OK', [('Content-type', 'text/xml')])
                try:
                    wsdl_content = service.wsdl(url)

                    # implementation hook
                    self.onWsdl(environ, wsdl_content)
                except Exception, e:

                    # implementation hook
                    buffer = cStringIO.StringIO()
                    traceback.print_exc(file=buffer)
                    buffer.seek(0)
                    stacktrace = str(buffer.read())
                    faultStr = ElementTree.tostring(make_soap_fault(str(e),
                        detail=stacktrace), encoding=string_encoding)
                    exceptions(faultStr)
                    self.onWsdlException(environ, e, faultStr)
                    # initiate the response
                    start_response('500 Internal Server Error',
                                   [('Content-type', 'text/xml'),
                                    ('Content-length', str(len(faultStr)))])
                    return [faultStr]

                reset_request()
                return [wsdl_content]

            if environ['REQUEST_METHOD'].lower() != 'post':
                start_response('405 Method Not Allowed', [('Allow', 'POST')])
                return ''

            input = environ.get('wsgi.input')
            length = environ.get("CONTENT_LENGTH")
            body = input.read(int(length))

            methodname = environ.get("HTTP_SOAPACTION")

            debug('\033[92m'+ methodname +'\033[0m')
            debug(body)

            body = collapse_swa(environ.get("CONTENT_TYPE"), body)

            # deserialize the body of the message
            try:
                payload, header = from_soap(body)
            except SyntaxError, e:
                payload = None
                header = None

            if payload is not None and len(payload) > 0:
                methodname = payload.tag
            else:
                # check HTTP_SOAPACTION
                methodname = environ.get("HTTP_SOAPACTION")
                if methodname.startswith('"') and methodname.endswith('"'):
                    methodname = methodname[1:-1]
                if methodname.find('/') >0:
                    methodname = methodname.split('/')[1]

            request.header = header

            # retrieve the method descriptor
            descriptor = service.get_method(methodname)
            func = getattr(service, descriptor.name)
            
            if payload is not None and len(payload) > 0:
                params = descriptor.inMessage.from_xml(*[payload])
            else:
                params = ()
            # implementation hook
            self.onMethodExec(environ, body, params,
                descriptor.inMessage.params)

            # call the method
            retval = func(*params)

            # transform the results into an element
            # only expect a single element
            results = None
            if not (descriptor.isAsync or descriptor.isCallback):
                results = descriptor.outMessage.to_xml(*[retval])

            # implementation hook
            self.onResults(environ, results, retval)

            # grab any headers that were included in the request
            response_headers = None
            if hasattr(request, 'response_headers'):
                response_headers = request.response_headers

            # construct the soap response, and serialize it
            envelope = make_soap_envelope(results, tns=service.__tns__,
                header_elements=response_headers)
            resp = ElementTree.tostring(envelope, encoding=string_encoding)
            headers = {'Content-Type': 'text/xml'}

            if descriptor.mtom:
                headers, resp = apply_mtom(headers, resp,
                    descriptor.outMessage.params, (retval, ))

            if 'CONTENT_LENGTH' in environ:
                del environ['CONTENT_LENGTH']

            # initiate the response
            start_response('200 OK', headers.items())

            self.onReturn(environ, resp)

            debug('\033[91m'+ "Response" + '\033[0m')
            debug(resp)

            # return the serialized results
            reset_request()
            return [resp]

        except Fault, e:
            # grab any headers that were included in the request
            response_headers = None
            if hasattr(request, 'response_headers'):
                response_headers = request.response_headers

            # The user issued a Fault, so handle it just like an exception!
            fault = make_soap_fault(
                e.faultstring,
                e.faultcode,
                e.detail,
                header_elements=response_headers)

            faultStr = ElementTree.tostring(fault, encoding=string_encoding)

            exceptions(faultStr)

            self.onException(environ, e, faultStr)
            reset_request()

            # initiate the response
            start_response('500 Internal Server Error',
                [('Content-type', 'text/xml')])
            return [faultStr]

        except Exception, e:
            # Dump the stack trace to a buffer to be sent
            # back to the caller

            # capture stacktrace
            buffer = cStringIO.StringIO()
            traceback.print_exc(file=buffer)
            buffer.seek(0)
            stacktrace = str(buffer.read())

            faultstring = str(e)
            if methodname:
                faultcode = faultCode = '%sFault' % methodname
            else:
                faultcode = 'Server'
            detail = stacktrace

            faultStr = ElementTree.tostring(make_soap_fault(faultstring,
                faultcode, detail), encoding=string_encoding)
            exceptions(faultStr)

            self.onException(environ, e, faultStr)
            reset_request()

            # initiate the response
            start_response('500 Internal Server Error',
                [('Content-type', 'text/xml')])
            return [faultStr]


class SimpleWSGISoapApp(WSGISoapApp, SoapServiceBase):
    '''
    This object is a VERY simple extention of the base WSGISoapApp.
    It subclasses both WSGISoapApp, and SoapServiceBase, so that
    an object can simply subclass this single object, and it will
    be both a wsgi application and a soap service.  This is convenient
    if you want to only expose some functionality, and dont need
    complex handler mapping, and all of the functionality can be put
    in a single class.
    '''

    def __init__(self):
        WSGISoapApp.__init__(self)
        SoapServiceBase.__init__(self)

    def getHandler(self, environ):
        return self
