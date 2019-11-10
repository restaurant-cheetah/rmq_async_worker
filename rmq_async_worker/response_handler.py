import pika

import abc

class ResponseHandler(abc.ABC):
    @abc.abstractmethod
    def response(self):
        pass
